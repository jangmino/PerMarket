import random
import argparse
import sys
import csv
import math
import numpy as np

def sampleDeal(dealHist):
  '''
  First step: sample deal proportional to user histograms
  After sampling, user hist will be decreased by one.
  :param hist:
  :return:
  '''
  x = np.random.choice(len(dealHist), p=dealHist/dealHist.sum())
  return x

def BuildCategoryToUsers(fpath, categoryToIdx, logStep = 1000000):
  numLines = 0
  C = len(categoryToIdx)
  SortedP = {}
  sortedIndexDic = {}
  categoryMatrix = None
  sys.stderr.write("...now reading.\n")
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if numLines == 1:
        dimUser, dimCategory = int(row[0]), int(row[1])
        categoryMatrix = np.zeros((dimUser, dimCategory), dtype=np.float32)
        continue
      if numLines % logStep == 0: sys.stderr.write("......{} lines are read.\n".format(numLines))
      if len(row) != C+1: raise RuntimeError("user summary's row should be size {}, but :{}:".format(C+1, ' '.join(row)))
      userIdx = int(row[0])
      vec = np.asarray([float(v) for v in row[1:]], dtype=np.float32)
      categoryMatrix[userIdx,:] = vec/vec.sum()

    sys.stderr.write("...now sorting.\n")
    for c in range(C):
      ii = np.argsort(categoryMatrix[:,c])
      indices = []
      for i in reversed(ii):
        if categoryMatrix[i, c] < 1e-6:
          break
        indices.append(i)
      #sortedIndexDic[c] = OrderedDict(zip(indices, categoryMatrix[indices, c].tolist()))
      sortedIndexDic[c] = indices
    sys.stderr.write("...done\n")

    return categoryMatrix, sortedIndexDic

def BuildDealSummary(fpath, skipFirstLine = True):
  dealToCategory = {}
  categoryToIdx = {}
  dealToIdx = {}
  numLines = 0
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if len(row) != 2: raise RuntimeError("DealSummary's row should be size two, but :{}:".format(' '.join(row)))
      deal, category = row[0], row[1]
      if deal not in dealToIdx:
        dealToIdx[deal] = len(dealToIdx)
      if category not in categoryToIdx:
        categoryToIdx[category] = len(categoryToIdx)

      dealIdx, categoryIdx = dealToIdx[deal], categoryToIdx[category]
      if dealIdx not in dealToCategory:
        dealToCategory[dealIdx] = categoryIdx

  return dealToCategory, dealToIdx, categoryToIdx

def getNextMaxScoredUser(sortedIndex, head, assignedSet):
  while head < len(sortedIndex):
    if sortedIndex[head] in assignedSet:
      head += 1
    else:
      return (sortedIndex[head], head+1)
  return (-1, head)

def doLoop(dealHist, catHist, dealToCategory, categoryMatrix, sortedIndexDic):
  dimDeal, dimUser, dimCategory = len(dealHist), categoryMatrix.shape[0], categoryMatrix.shape[1]
  recSet = {}
  BulkSize = max(1, dimUser // 100)
  notAssigend = {}
  headSortedIndexDic = {}
  for c in range(dimCategory): headSortedIndexDic[c] = 0

  while dimUser > 0 and dimDeal > 0 and dealHist.sum() > 0:
    ## step 1
    d = sampleDeal(dealHist)
    dealHist[d] -= 1

    if (dimUser - dealHist.sum()) % BulkSize == 0: sys.stderr.write("{:.2f}% is processed.\n".format(100*(dimUser - dealHist.sum())/dimUser))

    ## step 2
    c = dealToCategory[d]

    ## step 3
    (u, nexthead) = getNextMaxScoredUser(sortedIndexDic[c], headSortedIndexDic[c], recSet)
    headSortedIndexDic[c] = nexthead
    if u >= 0:
      if u not in recSet:
        recSet[u] = d
      else:
        raise RuntimeError("user %d is already assigned to deal %d" % (u, d))
    else:
      if d not in notAssigend: notAssigend[d] = 1
      else: notAssigend[d] = 1

    ## step 4

  return recSet, notAssigend

def WriteUserSummary(fpath, userDic, dimCategory):
  '''

  :param fpath:
  :param userDic: user -> histograms of category ( order counts )
  :return:
  '''

  svec = fpath.split('.')
  if len(svec) > 0:
    fpath_ii = ".".join(svec[0:-1]) + "_ii." + svec[-1]
  else:
    fpath_ii = fpath + "_ii.csv"

  n = 0
  data = []
  with open(fpath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([len(userDic), dimCategory])
    for user, counts in userDic.items():
      writer.writerow([n] + [count for count in counts])
      data.append((user, n))
      n += 1

  with open(fpath_ii, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(("user", "id"))
    for user, n in data:
      writer.writerow((user, n))


def WriteResult(fpath, recResult):
  with open(fpath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['user', 'deal'])
    for user, deal in recResult.items():
      writer.writerow([user, deal])

def ReadIndirectDic(fpath, skipFirstLine = True, logStep = 1000000):
  idxToUser = {}
  numLines = 0
  C = len(categoryToIdx)
  SortedP = {}
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if numLines % logStep == 0: sys.stderr.write("......{} lines are read.\n".format(numLines))
      if len(row) != 2: raise RuntimeError("ReadIndirectDic's row should be size two, but :{}:".format(' '.join(row)))
      user, idx = row[0], int(row[2].replace(',',''))

      if idx not in idxToUser:
        idxToUser[idx] = user

  return idxToUser

## main 설계
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-s", "--summary", help="the file path of user summary")
  parser.add_argument("-d", "--deal", help="the file path of deal-category information")
  parser.add_argument("-o", "--outputrecom", help="the file output path of indirect recommendation")
  args = parser.parse_args()

  if args.summary == None or args.deal == None or args.outputrecom == None:
    parser.print_usage()
    sys.exit(1)

  dealToCategory, dealToIdx, categoryToIdx = BuildDealSummary(args.deal)
  categoryMatrix, sortedIndexDic = BuildCategoryToUsers(args.summary, categoryToIdx)
  dimDeal, dimUser, dimCategory = len(dealToCategory), categoryMatrix.shape[0], categoryMatrix.shape[1]
  print("#users: {}, #deals: {}, #categories: {}".format(dimUser, dimDeal, dimCategory))

  # prepare
  dealHist = np.ones((dimDeal,), dtype=np.int32) * math.ceil(dimUser / dimDeal)
  catHist = np.zeros((dimCategory,), dtype=np.int32)
  for d, h in zip(range(dimDeal), dealHist):
      catHist[dealToCategory[d]] += h

  # # 테스트 코드
  # dealToCategory = {0: 0, 1: 0, 2: 0, 3: 1, 4: 1}
  # categoryMatrix = np.array([(0.1, 0.9),
  #                            (0.2, 0.8),
  #                            (0.3, 0.7),
  #                            (0.4, 0.6),
  #                            (0.5, 0.5),
  #                            (0.6, 0.4),
  #                            (0.7, 0.3),
  #                            (0.8, 0.2),
  #                            (0.9, 0.1),
  #                            (0.95, 0.05)
  #                            ])
  # sortedIndexDic = {}
  # for c in range(2):
  #   sortedIndexDic[c] = [i for i in reversed(np.argsort(categoryMatrix[:, c]))]
  # dealHist = np.array([2,2,2,2,2], dtype=np.int32)
  # catHist = np.array([5,5], dtype=np.int32)
  # # 테스트 코드

  assigned, notAssgigned = doLoop(dealHist, catHist, dealToCategory, categoryMatrix, sortedIndexDic)


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

  WriteResult(args.outputrecom, assigned)

  sys.exit(0)