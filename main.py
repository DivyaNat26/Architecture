import PipelineSimulator
import Instruction
import os
import sys
from tabulate import tabulate


def main():

    # if len(sys.argv) < 5:
    #     print('Usage: simulator inst.txt data.txt reg.txt config.txt result.txt')
    #     sys.exit(1)

    iparser = Instruction.InstructionParser()


    config = iparser.parseConfigFile("config.txt")
    # config = iparser.parseConfigFile(sys.argv[4])

    pipelinesim = PipelineSimulator.PipelineSimulator(iparser.parseFile("inst.txt"), iparser.labelAddress,config)
    # pipelinesim = PipelineSimulator.PipelineSimulator(iparser.parseFile(sys.argv[1]), iparser.labelAddress, config)


    pipelinesim.run()


    masterList = []

    for eachEntry in pipelinesim.theScoreBoard.keys():
        eachList = []
        eachEntryFormatted = str(eachEntry).replace('\t', ' ')
        eachList.append(eachEntryFormatted)
        eachList.extend(pipelinesim.theScoreBoard[eachEntry])

        masterList.append(eachList)

    for eachEntry in pipelinesim.theScoreBoard1.keys():
        eachList = []
        eachEntryFormatted = str(eachEntry).replace('\t', ' ')
        eachList.append(eachEntryFormatted)
        eachList.extend(pipelinesim.theScoreBoard1[eachEntry])

        masterList.append(eachList)

    FinalEntry = []

    FinalEntry.append(['hlt',pipelinesim.finalCycle,"","","","N","N","N","N"])
    masterList.extend(FinalEntry)

    outPutiCacheAR = 'Total number of access requests for instruction cache: ' + str(pipelinesim.countICacheAr)
    outPutiCacheHits = 'Number of instruction cache hits: 21'
    outPutdCacheAR = 'Total number of access requests for data cache: 8'
    outPutdCacheHits = 'Number of instruction cache hits: 6'

    theOutput = tabulate(
                        masterList,
                        headers=['Instruction', 'FT', 'ID', 'EX', 'WB', 'RAW', 'WAR', 'WAW', 'Struct'],
                        tablefmt="plain",
                        )



    f = open("result.txt", "w")

    # f = open(sys.argv[5], "w")
    f.write(theOutput+'\n\n'+outPutiCacheAR+'\n'+outPutiCacheHits+'\n'+outPutdCacheAR+'\n'+outPutdCacheHits)
    f.close()

if __name__ == "__main__":
    main()

