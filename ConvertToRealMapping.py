import argparse
import sys
import csv
import math
import numpy as np

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

def ReadIndirectDic(fpath, skipFirstLine = True, logStep = 1000000):
  idxToUser = {}
  numLines = 0
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if numLines % logStep == 0: sys.stderr.write(".")
      if len(row) != 2: raise RuntimeError("ReadIndirectDic's row should be size two, but :{}:".format(' '.join(row)))
      user, idx = row[0], int(row[1].replace(',',''))

      if idx not in idxToUser:
        idxToUser[idx] = user

  sys.stderr.write("{} are read.\n".format(numLines))
  return idxToUser

def Convert(fpath_indirect, fpath, idxToUser, idxToDeal, skipFirstLine = True, logStep = 1000000):
    numLines = 0
    with open(fpath_indirect, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        with open(fpath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user', 'deal'])

            for row in reader:
                numLines += 1
                if skipFirstLine == True and numLines == 1: continue
                if numLines % logStep == 0: sys.stderr.write(".")
                if len(row) != 2: raise RuntimeError(
                    "Convert's row should be size two, but :{}:".format(' '.join(row)))
                idxUser, idxDeal = int(row[0]), int(row[1])

                user = idxToUser[idxUser]
                deal = idxToDeal[idxDeal]

                writer.writerow((user, deal))

    sys.stderr.write("{} are done.\n".format(numLines))

## main 설계
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-m", "--mappingtable", help="the file path of user-index mapping table")
  parser.add_argument("-i", "--indrectrecom", help="the file path of indirect recommendation table")
  parser.add_argument("-d", "--deal", help="the file path of deal-category information")
  parser.add_argument("-r", "--realrecom", help="the file path of real recommendation table")
  args = parser.parse_args()

  if args.mappingtable == None or args.deal == None or args.indrectrecom == None or args.realrecom == None:
    parser.print_usage()
    sys.exit(1)

  dealToCategory, dealToIdx, categoryToIdx = BuildDealSummary(args.deal)
  idxToUser = ReadIndirectDic(args.mappingtable)
  idxToDeal = {v:k for k, v in dealToIdx.items()}

  Convert(args.indrectrecom, args.realrecom, idxToUser, idxToDeal)

  sys.exit(0)