import random
import argparse
import sys
import csv
import math
import time
import numpy as np
import pandas as pd

def sampleDeal(dealHist):
  '''
  First step: sample deal proportional to user histograms
  After sampling, user hist will be decreased by one.
  :param hist:
  :return:
  '''
  x = np.random.choice(len(dealHist), p=dealHist/dealHist.sum())
  return x

def getNextMaxScoredUser(sortedIndex, head, assignedSet):
  while head < len(sortedIndex):
    if sortedIndex[head] in assignedSet:
      head += 1
    else:
      return (sortedIndex[head], head+1)
  return (-1, head)

def doLoop(deal_df, dealHist, dimUser, sorted_categories):
  dimDeal, dimCategory = len(deal_df), len(sorted_categories)
  recSet = {}
  BulkSize = max(1, dimUser // 10)
  notAssigend = {}
  headSortedIndexDic = {}
  for c in sorted_categories.keys(): headSortedIndexDic[c] = 0

  ts_start = time.time()

  while dimUser > 0 and dimDeal > 0 and dealHist.sum() > 0:
    ## step 1
    didx = sampleDeal(dealHist)
    dealHist[didx] -= 1

    if (dimUser - dealHist.sum()) % BulkSize == 0:
      sys.stderr.write("{:.2f}% is processed...".format(100*(dimUser - dealHist.sum())/dimUser))
      sys.stderr.write("{0:.2f} sec\n".format(time.time() - ts_start))
      ts_start = time.time()

    ## step 2
    c = deal_df.loc[didx,'category']

    ## step 3
    (u, nexthead) = getNextMaxScoredUser(sorted_categories[c], headSortedIndexDic[c], recSet)
    headSortedIndexDic[c] = nexthead
    if u >= 0:
      if u not in recSet:
        recSet[u] = deal_df.loc[didx,'deal_id']
      else:
        raise RuntimeError("user %d is already assigned to deal %d" % (u, d))
    else:
      if didx not in notAssigend: notAssigend[didx] = 1
      else: notAssigend[didx] = 1

    ## step 4

  return recSet, notAssigend

def WriteResult(fpath, recResult):
  with open(fpath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['user', 'deal'])
    for user, deal in recResult.items():
      writer.writerow([user, deal])

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--input", help="the file path of user-order information")
  parser.add_argument("-d", "--deal", help="the file path of deal-category information")
  parser.add_argument("-o", "--outputrecom", help="the file output path of recommendation")
  args = parser.parse_args()

  if args.input == None or args.deal == None or args.outputrecom == None:
    parser.print_usage()
    sys.exit(1)

  ts_start = time.time()
  sys.stderr.write("loading data...")
  deal_df = pd.read_csv(args.deal, thousands=',', dtype={'deal_id': np.int32, 'category': str})
  user_df = pd.read_csv(args.input, thousands=',',
                        dtype={'m_id': np.int32, 'category': str, 'cnt': np.int32})
  sys.stderr.write("{0:.2f} sec\n".format(time.time() - ts_start))

  # 피봇 생성
  ts_start = time.time()
  sys.stderr.write("making pivot...")
  x = user_df.pivot(index='m_id', columns='category', values='cnt')
  sys.stderr.write("{0:.2f} sec\n".format(time.time() - ts_start))

  # 필요 없는 컬럼 지움 (nan, none, 상품권/e쿠폰 등등.... 관련없는 카테고리)
  removed_columns = list(i for i in x.columns if i not in deal_df['category'].unique())
  x.drop(removed_columns, axis=1, inplace=True)
  x.fillna(value=0.0, inplace=True)

  y = x.div(x.sum(axis=1), axis=0)
  y.fillna(value=0.0, inplace=True)
  
  # 정렬
  ts_start = time.time()
  sys.stderr.write("constructing sorted category informations...")
  sorted_categories = {}
  for c in y.columns:
      temp = y[c].sort_values(ascending=False)
      # 값이 0인 인덱스는 필요 없다.
      sorted_categories[c] = temp[temp > 0].index
  sys.stderr.write("{0:.2f} sec\n".format(time.time() - ts_start))

  dimDeal = len(deal_df)
  dimUser = len(y)
  deal_df['hist'] = np.ones((dimDeal,), dtype=np.int32) * math.ceil(dimUser / dimDeal)
  dealHist = np.ones((dimDeal,), dtype=np.int32) * math.ceil(dimUser / dimDeal)
  #category_df = deal_df.groupby('category').sum()['hist'].to_frame().reset_index()

  ts_start = time.time()
  sys.stderr.write("start matching...\n")
  assigned, notAssgigned = doLoop(deal_df, dealHist, dimUser, sorted_categories)
  sys.stderr.write("total...{0:.2f} sec\n".format(time.time() - ts_start))

  # verify
  #dealAssigned = {}
  numUserAssigned = 0
  for user, deal in assigned.items():
    #if deal not in dealAssigned: dealAssigned[deal] = 1
    #else: dealAssigned[deal] += 1
    numUserAssigned += 1
  # for deal, cnt in dealAssigned.items():
  #   sys.stderr.write("{}:{}\n".format(deal, cnt))

  sys.stderr.write("\n{} users are assgined over {}.\n".format(numUserAssigned, dimUser))

  ts_start = time.time()
  sys.stderr.write("writing results...")
  WriteResult(args.outputrecom, assigned)
  sys.stderr.write("{0:.2f} sec\n".format(time.time() - ts_start))

  sys.stderr.write("\ndone...\n")

  sys.exit(0)
