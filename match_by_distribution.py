import random
import argparse
import sys
import csv
import math
from collections import OrderedDict
import numpy as np
from scipy.special import digamma
from scipy.special import gammaln

class DirMult:
  def __init__(self, dim):
    prior = np.zeros(dim,)
    observations = np.zeros(dim,)

class Hist:
  def __init__(self, total_=0, vec_={}):
    self.total = total_
    self.vec = vec_

def BuildDealSummary(fpath, skipFirstLine = True):
  dealDic = {}
  numLines = 0
  dealToIdx = {}
  categoryToIdx = {}
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if len(row) != 2: raise RuntimeError("DealSummary's row should be size two, but :{}:".format(' '.join(row)))
      deal, category = row[0], row[1]
      if deal not in dealDic:
        dealDic[deal] = category
      if deal not in dealToIdx:
        dealToIdx[deal] = len(dealToIdx)
      if category not in categoryToIdx:
        categoryToIdx[category] = len(categoryToIdx)

  return dealDic, dealToIdx, categoryToIdx

def BuildUserSummary(fpath, categoryToIdx, skipFirstLine = True, logStep = 1000000):
  UserDic = {}
  numLines = 0
  C = len(categoryToIdx)
  total = np.zeros(C,)

  userToIdx = {}

  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      #if numLines == 10000: break
      if skipFirstLine == True and numLines == 1: continue
      if numLines % logStep == 0: sys.stderr.write("......{} lines are read.\n".format(numLines))
      if len(row) != 3: raise RuntimeError("DealSummary's row should be size two, but :{}:".format(' '.join(row)))
      user, category, count = row[0], row[1], int(row[2].replace(',',''))

      if category not in categoryToIdx:
        continue
      catIdx = categoryToIdx[category]
      if user not in UserDic:
        UserDic[user] = np.zeros(C,)
      UserDic[user][catIdx] += count

      if user not in userToIdx:
        userToIdx[user] = len(userToIdx)

      total[catIdx] += count

  return UserDic, total, userToIdx, numLines

def BuildCategoryRankedUsers(UserDic, categoryToIdx, userToIdx):
  categoryDic = {}
  for c in range(len(categoryToIdx)): categoryDic[c] = []
  for user, vec in UserDic.items():
    for ii in np.argsort(vec):
      categoryDic[ii].append((userToIdx[user], vec[ii]))
  sys.stderr.write("Category Dictionary was prepared...\n")

  for c in range(len(categoryToIdx)):
    categoryDic[c] = OrderedDict(sorted(categoryDic[c], key=lambda t:-1*t[1]))
  sys.stderr.write("Category Dictionary was sorted...\n")

  return categoryDic


def argmaxByDirchletRatio(p, q, alpha=1.0):
  ## http://bariskurt.com/kullback-leibler-divergence-between-two-dirichlet-and-beta-distributions/

  x = p + alpha
  y = q + alpha

  score = gammaln(y) - gammaln(x) +  (x - y) * (digamma(x) - digamma(x.sum()))
  score.argmax()

def doLoop(dealDic, total, userDic, categoryToIdx, numUsers, numDeals):
  bulkSize = max(1, numUsers//100)
  n = 0
  while numUsers > 0 and numDeals > 0 and len(userDic) > 0 and n < numUsers:
    score = argmaxByDirchletRatio(total, total)
    n += 1
    if n % bulkSize == 0: sys.stderr.write("{:.2f}% is processed.\n".format(100*n/numUsers))

  sys.stderr.write("\n")

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

  dealDic, dealToIdx, categoryToIdx = BuildDealSummary(args.deal)
  userDic, total, userToIdx, numLines = BuildUserSummary(args.user, categoryToIdx)
  categoryDic = BuildCategoryRankedUsers(userDic, categoryToIdx, userToIdx)

  while True:
    x=1

  doLoop(dealDic, total, userDic, categoryToIdx, len(userDic), len(dealDic))


  #
  # numDeals, numUsers = len(D), len(UserDic)
  # print("#users: {}, #deals: {}, #lines: {}".format(numUsers, numDeals, numLines))
  #
  # # prepare
  # O = Hist(numUsers, {})
  # for deal in D.keys():
  #   O.vec[deal] = math.ceil(numUsers / numDeals)
  #
  # assigned, notAssgigned = doLoop(O, sortedP, D, numUsers, numDeals)
  #
  # # verify
  # dealAssigned = {}
  # numUserAssigned = 0
  # for user, deal in assigned.items():
  #   if deal not in dealAssigned: dealAssigned[deal] = 1
  #   else: dealAssigned[deal] += 1
  #   numUserAssigned += 1
  # # for deal, cnt in dealAssigned.items():
  # #   sys.stderr.write("{}:{}\n".format(deal, cnt))
  # sys.stderr.write("\n{} users are assgined over {}.\n".format(numUserAssigned, numUsers))
  #
  # WriteResult(args.output, assigned)