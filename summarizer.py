import argparse
import sys
import csv
import numpy as np

def BuildUserInformation(fpath, categoryToIdx, skipFirstLine = True, logStep = 1000000):
  UserDic = {}
  numLines = 0
  C = len(categoryToIdx)
  SortedP = {}
  with open(fpath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
      numLines += 1
      if skipFirstLine == True and numLines == 1: continue
      if numLines % logStep == 0: sys.stderr.write("......{} lines are read.\n".format(numLines))
      if len(row) != 3: raise RuntimeError("DealSummary's row should be size two, but :{}:".format(' '.join(row)))
      user, category, count = row[0], row[1], int(row[2].replace(',',''))

      if category not in categoryToIdx:
        continue
      catIdx = categoryToIdx[category]

      if user not in UserDic:
        UserDic[user] = np.zeros((C,), dtype=np.int32)
      UserDic[user][catIdx] += count
  return UserDic

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

def WriteUserSummaryAndMapping(fpath, fpath_mapping, userDic, dimCategory):
  '''

  :param fpath:
  :param userDic: user -> histograms of category ( order counts )
  :return:
  '''

  n = 0
  data = []
  with open(fpath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([len(userDic), dimCategory])
    for user, counts in userDic.items():
      writer.writerow([n] + [count for count in counts])
      data.append((user, n))
      n += 1

  with open(fpath_mapping, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(("user", "id"))
    for user, n in data:
      writer.writerow((user, n))

## main 설계
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--input", help="the file path of user-order information")
  parser.add_argument("-d", "--deal", help="the file path of deal-category information")
  parser.add_argument("-o", "--outputsummary", help="the output file path of summary")
  parser.add_argument("-m", "--outputmapping", help="the output file path of mapping bewteen user-idx")
  args = parser.parse_args()

  if args.input == None or args.deal == None or args.outputsummary == None or args.outputmapping == None:
    parser.print_usage()
    sys.exit(1)

  dealToCategory, dealToIdx, categoryToIdx = BuildDealSummary(args.deal)
  UserDic = BuildUserInformation(args.input, categoryToIdx)
  WriteUserSummaryAndMapping(args.outputsummary, args.outputmapping, UserDic, len(categoryToIdx))

  sys.exit(0)
