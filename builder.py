import random
import argparse
import sys
import csv
import math
from collections import OrderedDict


class Hist:
  def __init__(self, total_=0, vec_={}):
    self.total = total_
    self.vec = vec_

def sample(hist):
  x = random.randrange(hist.total)
  cumsum = 0
  for k, v in hist.vec.items():
    cumsum += v
    if x < cumsum: # got it
      return k
  raise RuntimeError("Reached End while Sampling")

def sample_user(sortedHist):
  if len(sortedHist) == 0: RuntimeError("SortedHist should not be empty")
  return sortedHist.popitem(True)


def sample_deal(hist):
  '''
  First step: sample deal proportional to user histograms
  After sampling, user hist will be decreased by one.
  :param hist:
  :return:
  '''
  x = random.randrange(hist.total)
  cumsum = 0
  for k, v in hist.vec.items():
    cumsum += v
    if x < cumsum: # got it
      hist.total -= 1
      hist.vec[k] -= 1
      if hist.total < 0: raise RuntimeError("hist.Total gets below Zero.")
      if v < 0: raise RuntimeError("vec[d] gets below Zero.")
      return k
  raise RuntimeError("Reached End while Sampling")

def AdjustAfterSampling(P, u):
  '''
  P[c] = hist.total, hist.vec

  :param P:
  :param c:
  :param u:
  :return:
  '''

  for c, hist in P.items():
    if u in hist.vec:
      hist.total -= hist.vec[u]
      if hist.total < 0: raise RuntimeError("hist[%d].Total gets below Zero" % (c) )
      del hist.vec[u]

def AdjustSortedPAfterSampling(SortedP, u):
  for c, sortedHist in SortedP.items():
    if u in sortedHist: del sortedHist[u]


def BuildUserSummary(fpath, skipFirstLine = True, logStep = 1000000):
  P = {}
  UserDic = {}
  numLines = 0
  SortedP = {}
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if numLines % logStep == 0: sys.stderr.write("......{} lines are read.\n".format(numLines))
      if len(row) != 3: raise RuntimeError("DealSummary's row should be size two, but :{}:".format(' '.join(row)))
      user, category, count = row[0], row[1], int(row[2].replace(',',''))

      if user not in UserDic:
        UserDic[user] = 1
      else:
        UserDic[user] += 1
      if category not in P:
        P[category] = Hist(count, {user: count})
      else:
        P[category].vec[user] = count
        P[category].total += count

    # Make OrderedDic
    sys.stderr.write("\nsorting histograms per category...")
    for c in list(P.keys()):
      SortedP[c] = OrderedDict(sorted(P[c].vec.items(), key=lambda t:t[1]))
      del P[c]
    sys.stderr.write("done\n")

  return SortedP, UserDic, numLines


def BuildDealSummary(fpath, skipFirstLine = True):
  D = {}
  numLines = 0
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if len(row) != 2: raise RuntimeError("DealSummary's row should be size two, but :{}:".format(' '.join(row)))
      deal, category = row[0], row[1]
      if deal not in D:
        D[deal] = category

  return D

def doLoop(O, P, DealToCategory, numUsers, numDeals):
  recSet = {}
  BulkSize = max(1, numUsers // 100)
  notAssigend = {}
  while numUsers > 0 and numDeals > 0 and O.total > 0:
    ## step 1
    d = sample_deal(O)

    if (numUsers - O.total) % BulkSize == 0: sys.stderr.write("{:.2f}% is processed.\n".format(100*(numUsers - O.total)/numUsers))

    ## step 2
    c = DealToCategory[d]

    ## step 3
    if len(P[c]) > 0:
      u,cnt = sample_user(P[c])
      AdjustSortedPAfterSampling(P, u)

      if u not in recSet:
        recSet[u] = d
      else:
        raise RuntimeError("user %d is already assigned to deal %d" % (u, d))
    else:
      if d not in notAssigend: notAssigend[d] = 1
      else: notAssigend[d] = 1

    ## step 4

  return recSet, notAssigend


def WriteResult(fpath, recResult):
  with open(fpath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['user', 'deal'])
    for user, deal in recResult.items():
      writer.writerow([user, deal])

## main 설계
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-u", "--user", help="the file path of user-order summary")
  parser.add_argument("-d", "--deal", help="the file path of deal-category information")
  parser.add_argument("-o", "--output", help="the file path of output user-deal recommendation")
  args = parser.parse_args()

  if args.user == None or args.deal == None or args.output == None:
    parser.print_usage()
    sys.exit(1)

  D = BuildDealSummary(args.deal)
  sortedP, UserDic, numLines = BuildUserSummary(args.user)

  numDeals, numUsers = len(D), len(UserDic)
  print("#users: {}, #deals: {}, #lines: {}".format(numUsers, numDeals, numLines))

  # prepare
  O = Hist(numUsers, {})
  for deal in D.keys():
    O.vec[deal] = math.ceil(numUsers / numDeals)

  assigned, notAssgigned = doLoop(O, sortedP, D, numUsers, numDeals)

  # verify
  dealAssigned = {}
  numUserAssigned = 0
  for user, deal in assigned.items():
    if deal not in dealAssigned: dealAssigned[deal] = 1
    else: dealAssigned[deal] += 1
    numUserAssigned += 1
  # for deal, cnt in dealAssigned.items():
  #   sys.stderr.write("{}:{}\n".format(deal, cnt))
  sys.stderr.write("\n{} users are assgined over {}.\n".format(numUserAssigned, numUsers))

  WriteResult(args.output, assigned)