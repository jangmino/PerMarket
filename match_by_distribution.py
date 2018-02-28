import random
import argparse
import sys
import csv
import math
from collections import OrderedDict
import numpy as np

class DirMult:
  def __init__(self, dim):
    prior = np.zeros(dim,)
    observations = np.zeros(dim,)

class Hist:
  def __init__(self, total_=0, vec_={}):
    self.total = total_
    self.vec = vec_

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

def BuildUserSummary(fpath, categoryDic, skipFirstLine = True, logStep = 1000000):
  P = {}
  UserDic = {}
  numLines = 0
  SortedP = {}
  C = 10
  CategoryToIndex = {}
  prior = np.zeros(C,)

  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if numLines % logStep == 0: sys.stderr.write("......{} lines are read.\n".format(numLines))
      if len(row) != 3: raise RuntimeError("DealSummary's row should be size two, but :{}:".format(' '.join(row)))
      user, category, count = row[0], row[1], int(row[2].replace(',',''))

      if user not in UserDic:
        UserDic[user] = np.zeros(C,)
      idx = CategoryToIndex[category]
      UserDic[user][idx] += 1.0
      prior[idx] += 1.0

  return SortedP, UserDic, numLines


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

  # D = BuildDealSummary(args.deal)
  # sortedP, UserDic, numLines = BuildUserSummary(args.user)
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