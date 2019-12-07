from Instruction import *
import sys

import re




class PipelineSimulator(object):
    operations = {'add': '+', 'addi': '+', 'sub': '-', 'subi': '-', 'div': '/',
                  'and': '&', 'andi': '&', 'or': '|', 'ori': '|',
                  'add.d': '+', 'sub.d': '-', 'mul': '*', 'mul.d': '*', 'div.d': '/',
                  'dadd': '+', 'dsub': '-', 'dmul': '*', 'ddiv': '/',
                  'daddi': '+', 'dsubi': '-', 'dmuli': '*', 'ddivi': '/'}

    loadStoreUnit = {'l.d', 'lw'}
    addsubUnitaddsubUnit = {'add', 'sub', 'add.d', 'sub.d'}
    addSubImmiUnit = {'addi', 'daddi', 'subi', 'dsubi', 'dadd', 'dsub'}
    multiplicationUnit = {'mul', 'mul.d', 'dmul', 'dmuli'}
    divisionUnit = {'div', 'div.d', 'ddiv', 'ddivi'}

    def __init__(self, instrCollection,labelOfinstr,config):

        self.labelOfinstr = labelOfinstr
        self.config = config
        self.instrCount = 0
        self.cycles = 0
        self.hazardList = []
        self.__done = False
        self.branched = False
        self.stall = False
        self.theScoreBoard = {}
        self.theScoreBoard1 = {}
        self.theScoreBoard2 = {}
        self.dataCount = 0
        self.memStall = False
        self.MainMemCount = 0
        self.rawHaz = False
        self.MainMemCountFlag = False
        self.loadBuffer = []
        self.addCounter = 0
        self.addCounterFlag = False
        self.hasLoadInMem = False
        self.addedLoadBufferFlag = False
        self.WBBuffer = False
        self.hazardDict = {}
        self.hazardQueue = {}
        self.activeScoreBoard = []
        self.branchCount = 0
        self.isReset = False
        self.proceedAndEnd = False
        self.dCacheDict = {}
        self.iCacheMiss = False
        self.dCacheMissCount = 0
        self.iCacheMissCounter = 0
        self.cacheCounter = 0
        self.cacheCounterMainMem = 0
        self.hltCount = 0
        self.dontFetch = False
        self.loadBufferForCachePriority = []
        self.loadBufferForDCacheWait = []
        self.notCompletedList = []
        self.addToSB1 = False
        self.loadJustSteppingAside = []
        self.loadStoreUnit = {'l.d', 'lw'}
        self.printThisInstead = []

        self.countICacheAr = 0
        self.countICacheHit = 0

        self.countDCacheAR = 0
        self.countDCacheHit = 0



        self.dCacheMiss = False


        self.theCacheList = []

        self.instrLocationList = []

        self.doneAddEx = []
        self.adderUnitQueue = {}
        self.adderUnitQueuebusy = False

        self.addImmiUnitQueue = {}
        self.adderUnitImmiQueuebusy = False

        self.doneMulEx = []
        self.multiUnitQueue = {}
        self.MultiUnitQueuebusy = False

        self.doneDivEx = []
        self.DivUnitQueue = {}
        self.DivUnitQueuebusy = False

        self.iCacheExists = False
        self.dCacheExists = False

        self.pipeline = [None for x in range(0, 5)]

        theAddConfig = self.config['FP adder']
        self.theAddCycles = theAddConfig['cycles']
        self.isAddPipelined = theAddConfig['isPipelined']

        theMultiConfig = self.config['FP Multiplier']
        self.theMultiCycles = theMultiConfig['cycles']
        self.isMultiPipelined = theMultiConfig['isPipelined']

        theDivConfig = self.config['FP divider']
        self.theDivCycles = theDivConfig['cycles']
        self.isDivPipelined = theDivConfig['isPipelined']

        theMainMemConfig = self.config['Main memory']
        self.theMainMemCycles = theMainMemConfig['cycles']

        try:
            theiCacheConfig = self.config['I-Cache']
            self.theiCacheCycles = theiCacheConfig['cycles']
            self.iCacheExists = True
            if self.theiCacheCycles == 0:
                self.iCacheExists = False
        except KeyError:

            self.iCacheExists = False
            self.theiCacheCycles = 0

        try:

            theDCacheConfig = self.config['D-Cache']
            self.theDCacheCycles = theDCacheConfig['cycles']
            self.dCacheExists = True
            if self.theDCacheCycles == 0:
                self.dCacheExists = False
        except KeyError:

            self.dCacheExists = False
            self.theDCacheCycles = 0



        self.pipeline[0] = FetchStage(Nop, self)
        self.pipeline[1] = WriteStage(Nop, self)
        self.pipeline[2] = ReadStage(Nop, self)
        self.pipeline[3] = ExecStage(Nop, self)
        self.pipeline[4] = DataStage(Nop, self)

        # ex: {'$r0' : 0, '$r1' : 0 ... '$r31' : 0 }

        self.registers = dict([("r%s" % x, 0) for x in range(32)])


        self.FPregisters = dict([("f%s" % x, 0) for x in range(32)])
        self.mainmemory = dict([(x * 4, 0) for x in range(int(0xffc / 4))])

        self.programCounter = 0x00

        self.instrCollection = instrCollection

        y = 0
        for instr in self.instrCollection:


            self.instrLocation = 0x00 + y
            self.instrLocationList.append(self.instrLocation)
            self.mainmemory[self.instrLocation] = instr
            y += 4


        self.mainmemory = self.populateMainMemory(self.mainmemory)

        self.registers = self.populateIntegerRegisters(self.registers)




    def populateMainMemory(self, mainMemory):


        with open("data.txt") as f:
        # with open(sys.argv[2]) as f:
            data = list(filter((lambda x: x != '\n'), f.readlines()))


        y = 0
        for eachLine in data:
            mainMemory[0x100 + y] = int(eachLine, 2)
            y += 4


        return mainMemory

    def populateIntegerRegisters(self, registers):


        with open("reg.txt") as f:
        # with open(sys.argv[3]) as f:
            data = list(filter((lambda x: x != '\n'), f.readlines()))


        for k, v in registers.items():
            number = re.findall('\d+', k)
            registers[k] = int(data.__getitem__(int(number.__getitem__(0))), 2)


        return registers

    def step(self):

        self.cycles += 1


        if self.WBBuffer == True:
            self.pipeline[1] = WriteStage(Nop, self)

        if self.isReset == True:
            self.pipeline[0] = FetchStage(Nop, self)
            self.pipeline[2] = ReadStage(Nop, self)
            self.branched = False
            self.isReset = False




        if self.pipeline[4].instr is not Nop and 'l.d' in str(self.pipeline[4].instr) and self.MainMemCountFlag == True:
            self.pipeline[1] = WriteStage(self.pipeline[4].instr, self)
            self.pipeline[4] = DataStage(Nop, self)
            if self.loadBufferForDCacheWait and self.dCacheMiss==False:
                self.pipeline[4] = DataStage(self.loadBufferForDCacheWait.pop(0), self)
            self.MainMemCount = 0
            self.MainMemCountFlag = False

            if self.loadBuffer and self.dCacheMiss==False:

                self.pipeline[4] = DataStage(self.loadBuffer.pop(0), self)
                # self.pipeline[3] = ExecStage(Nop, self)
                self.addedLoadBufferFlag = True
            else:
                self.addedLoadBufferFlag = False



        if self.stall:
            self.pipeline[4] = DataStage(Nop, self)
            self.stall = False
        else:


            if self.pipeline[4].instr is not Nop and 'l.d' in str(self.pipeline[4].instr) and self.MainMemCountFlag == True:
                self.MainMemCount = 0

                if self.rawHaz is not True:
                    self.pipeline[4] = DataStage(self.pipeline[3].instr, self)

                    self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
                    self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)
                    self.pipeline[0] = FetchStage(None, self)

            else:
                if self.MainMemCount == 0 and self.addedLoadBufferFlag == False and not self.hazardQueue :
                    if self.doneAddEx:
                        if self.doneAddEx[0] in self.adderUnitQueue:
                            del self.adderUnitQueue[self.doneAddEx.pop(0)]
                        self.pipeline[1] = WriteStage(self.doneAddEx.pop(0), self)
                    elif self.doneMulEx:
                        self.pipeline[1] = WriteStage(self.doneMulEx.pop(0), self)
                    elif self.doneDivEx:
                        self.pipeline[1] = WriteStage(self.doneDivEx.pop(0), self)
                    elif str(self.pipeline[3].instr.op).strip() in self.loadStoreUnit and self.pipeline[3].instr not in self.loadBufferForDCacheWait:
                        self.pipeline[4] = DataStage(self.pipeline[3].instr, self)


                    if str(self.pipeline[4].instr.op).strip() in self.loadStoreUnit:
                        self.hasLoadInMem = True
                    else:
                        if self.loadJustSteppingAside:
                            self.pipeline[4] = DataStage(self.loadJustSteppingAside.pop(0),self)
                            self.hasLoadInMem = True
                        else:
                            self.hasLoadInMem = False
                    if self.iCacheMiss == False and self.dCacheMiss == False:
                        if self.pipeline[2].instr.op != 'bne' and self.pipeline[2].instr.op != 'hlt':
                            self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
                        self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)
                        if not(self.pipeline[0].instr.op == 'hlt' and self.pipeline[0].instr.op == 'hlt'):
                            self.pipeline[0] = FetchStage(None, self)
                    elif self.iCacheMiss == False:
                        self.pipeline[0] = FetchStage(None, self)
                    elif self.iCacheMiss == True and self.dCacheMiss == False:
                        if self.pipeline[2].instr.op != 'bne' and self.pipeline[2].instr.op != 'hlt':
                            self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
                            self.pipeline[2] = ReadStage(Nop, self)


                elif self.doneAddEx and self.MainMemCount == 0 and self.addedLoadBufferFlag==False:
                    self.pipeline[1] = WriteStage(self.doneAddEx.pop(0), self)
                    self.pipeline[3] = ExecStage(Nop,self)
                elif self.doneMulEx and self.MainMemCount == 0 and self.addedLoadBufferFlag==False:
                    self.pipeline[1] = WriteStage(self.doneMulEx.pop(0), self)
                    self.pipeline[3] = ExecStage(Nop, self)
                elif str(self.pipeline[2].instr.op).strip() in self.addsubUnitaddsubUnit and not self.hazardQueue:

                    self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
                    self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)
                    self.pipeline[0] = FetchStage(None, self)
                elif str(self.pipeline[2].instr.op).strip() in self.multiplicationUnit and not self.hazardQueue:

                    self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
                    self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)
                    self.pipeline[0] = FetchStage(None, self)
                elif self.dCacheMiss == True and self.pipeline[2].instr.op == 'l.d':
                    self.pipeline[3] = ExecStage(self.pipeline[2].instr, self)
                    self.pipeline[2] = ReadStage(Nop, self)
                    if self.iCacheExists == True and self.iCacheMiss == False:
                        self.pipeline[2] = ReadStage(self.pipeline[0].instr, self)



        for pi in self.pipeline:
            pi.advance()

        if (self.pipeline[1].instr.regWrite):

            if self.hazardList:
                thePopped = self.hazardList.pop(0)

                deleteThis = None
                for eachInst in self.hazardQueue.keys():
                    if eachInst.s1 == thePopped or eachInst.s2 == thePopped:
                        deleteThis = eachInst

                if deleteThis is not None:
                    del self.hazardQueue[deleteThis]


        self.checkDone()


        if self.branched and not self.hazardQueue:
                self.instrCount = 1
                self.programCounter = 0
                self.isReset = True

                if self.pipeline[2].instr.op == 'bne':
                   if self.branchCount == 0:
                       for eachEntry in self.theScoreBoard:
                           if "" in self.theScoreBoard[eachEntry] and 'bne' not in eachEntry and 'hlt' not in eachEntry:

                               self.notCompletedList.append(eachEntry.strip())


    def checkDone(self):

        self.__done = True
        for pi in self.pipeline:

            if self.iCacheMiss == False and self.pipeline[0].instr.op == 'hlt' and self.pipeline[2].instr is Nop:
                self.__done = True

            else:
                self.__done = False

    def run(self):

        pipe = 'Test'
        while not self.__done:
            self.step()
            self.debug()

    def debug(self):

        self.printStageCollection()
        self.printRegFile()

        self.printPipeline()

        self.printScoreBoard()

    def printScoreBoard(self):

        theList = ["", "", "", "", "", "", "", ""]


        fetchPrint = repr(self.pipeline[0]).split(":")
        readPrint = repr(self.pipeline[2]).split(":")
        executePrint = repr(self.pipeline[3]).split(":")
        memPrint = repr(self.pipeline[4]).split(":")
        writePrint = repr(self.pipeline[1]).split(":")

        thePipelineList = []
        thePipelineList.append(fetchPrint)
        thePipelineList.append(readPrint)
        thePipelineList.append(executePrint)
        thePipelineList.append(memPrint)
        thePipelineList.append(writePrint)

        for eachPipe in thePipelineList:

            try:
                if self.branchCount == 0:
                    theList = self.theScoreBoard[eachPipe[1].strip()]
                elif self.branchCount == 1:
                    theList = self.theScoreBoard1[eachPipe[1].strip()]
                elif self.branchCount == 2:
                    theList = self.theScoreBoard2[eachPipe[1].strip()]
            except KeyError:



                if self.notCompletedList:
                    for eachEntry in self.notCompletedList:
                        doThis = "".join(str(eachPipe[1]).split())
                        andThis = "".join(eachEntry).split()
                        if doThis in andThis:

                            if eachPipe[1].strip() in self.theScoreBoard:
                                theList = self.theScoreBoard[eachPipe[1].strip()]
                                self.addToSB1 = True

                pass



            ############################ IF ################################

            if eachPipe[0].strip() == 'Fetch Stage' and 'None' not in eachPipe[1].strip():

                if 'hlt' in eachPipe[1].strip() and self.proceedAndEnd == True and self.iCacheMiss == False and self.__done==True:
                    self.finalCycle = self.cycles

                elif not self.hazardQueue and self.iCacheMiss==False:
                    theList[0] = self.cycles

                    theList[4] = 'N'
                    theList[5] = 'N'
                    theList[6] = 'N'
                    theList[7] = 'N'

                    if self.branchCount == 0:
                        self.theScoreBoard[eachPipe[1].strip()] = theList
                    elif self.branchCount == 1:
                        self.theScoreBoard1[eachPipe[1].strip()] = theList
                    elif self.branchCount == 2:
                        self.theScoreBoard2[eachPipe[1].strip()] = theList

            ############################ ID ################################

            elif eachPipe[0].strip() == 'Read from Register' and 'None' not in eachPipe[1].strip():
                if not self.hazardQueue:
                    theList[1] = self.cycles

                    if self.hazardDict:
                        for eachHaz in self.hazardDict.keys():
                            if eachPipe[1].strip() in str(eachHaz).strip():
                                if self.hazardDict[eachHaz] == 'raw':
                                    theList[4] = 'Y'

                    if self.branchCount == 0:
                        self.theScoreBoard[eachPipe[1].strip()] = theList
                    elif self.branchCount == 1:
                        self.theScoreBoard1[eachPipe[1].strip()] = theList
                    elif self.branchCount == 2:
                        self.theScoreBoard2[eachPipe[1].strip()] = theList

            ############################ EX ################################

            elif eachPipe[0].strip() == 'Execute Stage' and 'None' not in eachPipe[1].strip():

                matches = False

                for eachEntry in self.adderUnitQueue.keys():
                    eachEntryStr = "".join(str(eachEntry).split())
                    eachPipeEntry = "".join(eachPipe[1].split())
                    if eachEntryStr in eachPipeEntry:

                        matches = True

                for eachEntry in self.multiUnitQueue.keys():
                    eachEntryStr = "".join(str(eachEntry).split())
                    eachPipeEntry = "".join(eachPipe[1].split())
                    if eachEntryStr in eachPipeEntry:

                        matches = True

                for eachEntry in self.doneAddEx:
                    eachEntryStr = "".join(str(eachEntry).split())
                    eachPipeEntry = "".join(eachPipe[1].split())
                    if eachEntryStr in eachPipeEntry:

                        matches = False

                for eachEntry in self.doneMulEx:
                    eachEntryStr = "".join(str(eachEntry).split())
                    eachPipeEntry = "".join(eachPipe[1].split())
                    if eachEntryStr in eachPipeEntry:

                        matches = False


                if matches == False:
                    if (eachPipe[1].strip().startswith('l.d') or eachPipe[1].strip().startswith('lw')) and self.printThisInstead:
                        theInstr = self.printThisInstead.pop(0)
                        theList = self.theScoreBoard1[theInstr]
                        theList[2] = self.cycles
                        if self.hazardDict:
                            for eachHaz in self.hazardDict.keys():
                                if eachPipe[1].strip() in str(eachHaz).strip():
                                    if self.hazardDict[eachHaz] == 'struct':
                                        theList[7] = 'Y'
                        self.theScoreBoard1[theInstr] = theList
                        self.pipeline[4] = DataStage(self.pipeline[3].instr, self)


                    else:

                        if self.addToSB1 == True:
                            theList[2] = self.cycles
                            if self.hazardDict:
                                for eachHaz in self.hazardDict.keys():
                                    if eachPipe[1].strip() in str(eachHaz).strip():
                                        if self.hazardDict[eachHaz] == 'struct':
                                            theList[7] = 'Y'

                            if self.branchCount == 0:
                                self.theScoreBoard[eachPipe[1].strip()] = theList
                            elif self.branchCount == 1:
                                self.theScoreBoard1[eachPipe[1].strip()] = theList
                            elif self.branchCount == 2:
                                self.theScoreBoard2[eachPipe[1].strip()] = theList
                            self.addToSB1 = False
                        else:
                            theList[2] = self.cycles
                            if self.hazardDict:
                                for eachHaz in self.hazardDict.keys():
                                    if eachPipe[1].strip() in str(eachHaz).strip():
                                        if self.hazardDict[eachHaz] == 'struct':
                                            theList[7] = 'Y'

                            if self.branchCount == 0:
                                self.theScoreBoard[eachPipe[1].strip()] = theList
                            elif self.branchCount == 1:
                                self.theScoreBoard1[eachPipe[1].strip()] = theList
                            elif self.branchCount == 2:
                                self.theScoreBoard2[eachPipe[1].strip()] = theList

            ############################ EX for L and S ################################

            elif eachPipe[0].strip() == 'Main Memory' and 'None' not in eachPipe[1].strip():
                if 'l.d' in eachPipe[1].strip() or 'lw' in eachPipe[1].strip():
                    if self.MainMemCountFlag == True and self.dCacheMiss==False:
                        theList[2] = self.cycles
                        if self.hazardDict:
                            for eachHaz in self.hazardDict.keys():
                                if eachPipe[1].strip() in str(eachHaz).strip():
                                    if self.hazardDict[eachHaz] == 'struct':
                                        theList[7] = 'Y'
                        if self.branchCount == 0:
                            self.theScoreBoard[eachPipe[1].strip()] = theList
                        elif self.branchCount == 1:
                            self.theScoreBoard1[eachPipe[1].strip()] = theList
                        elif self.branchCount == 2:
                            self.theScoreBoard2[eachPipe[1].strip()] = theList
                else:
                    pass

            ############################ WB ################################

            elif eachPipe[0].strip() == 'Write to Register' and 'None' not in eachPipe[1].strip():

                if self.addToSB1 == True:
                    theList[3] = self.cycles
                    self.theScoreBoard[eachPipe[1].strip()] = theList
                    self.notCompletedList.clear()
                    self.addToSB1 = False
                else:
                    theList[3] = self.cycles
                    if self.branchCount == 0:
                        self.theScoreBoard[eachPipe[1].strip()] = theList
                        if self.notCompletedList:
                            for eachEntry in self.notCompletedList:
                                doThis = "".join(str(eachPipe[1]).split())
                                andThis = "".join((eachEntry).split())
                                if doThis in andThis:
                                    self.notCompletedList.pop(0)

                    elif self.branchCount == 1:
                        self.theScoreBoard1[eachPipe[1].strip()] = theList
                    elif self.branchCount == 2:
                        self.theScoreBoard2[eachPipe[1].strip()] = theList

        if self.isReset==True:
            self.branchCount += 1



    def printPipeline(self):
        pipe = "test"
        # print("\n<Pipeline>")
        # print(repr(self.pipeline[0]))
        # print(repr(self.pipeline[2]))
        # print(repr(self.pipeline[3]))
        # print(repr(self.pipeline[4]))
        # print(repr(self.pipeline[1]))

    def printRegFile(self):
        pipe = "test"
        # # """
        # print("\n<Register File>")
        # for k, v in sorted(list(self.registers.items())):
        #     if len(k) != 3:
        #         print(k, " : ", v, end=' ')
        #     else:
        #         print("\n", k, " : ", v, end=' ')

    def printStageCollection(self):
        pipe = "test"
        # print("<Instruction Collection>")
        # for index, item in sorted(list(self.mainmemory.items())):
        #     if item != 0:
        #         print(index, ": ", str(item))


class PipelineStage(object):
    def __init__(self, instruction, simulator):
        self.instr = instruction
        self.simulator = simulator

    def advance(self):
        pass

    def __repr__(self):
        return str(self) + ':\t' + str(self.instr)


class PipelineStageList(object):
    def __init__(self, instruction, simulator):
        self.instr = []
        self.instr.append(instruction)
        self.simulator = simulator

    def advance(self):
        pass

    def __repr__(self):
        return str(self) + ':\t' + str(self.instr)


class FetchStage(PipelineStage):
    def advance(self):

        if not self.simulator.hazardQueue and self.simulator.iCacheMiss==False and self.simulator.dontFetch == False:

            if self.simulator.programCounter < (len(self.simulator.instrCollection) * 4 + 0xC8):

                self.simulator.instrCount += 1


                self.instr = self.simulator.mainmemory[self.simulator.programCounter]

                if self.simulator.iCacheExists == True:
                    self.simulator.countICacheAr += 1
                    if self.instr in self.simulator.theCacheList:
                        pipe = "Test"

                    else:


                        for i in range(4):
                            self.simulator.theCacheList.append(self.simulator.mainmemory[self.simulator.cacheCounterMainMem])
                            self.simulator.cacheCounterMainMem += 4
                        self.simulator.iCacheMiss = True
                        self.simulator.iCacheMissCounter = (self.simulator.theiCacheCycles + self.simulator.theMainMemCycles) * 2

            else:
                self.instr = Nop

            self.simulator.programCounter += 4

        if self.simulator.iCacheMissCounter != 0:
            self.simulator.iCacheMissCounter -= 1
        if self.simulator.iCacheMissCounter == 0 and self.simulator.iCacheExists == True:
            self.simulator.iCacheMiss = False


    def __str__(self):
        return 'Fetch Stage\t'


class ReadStage(PipelineStage):

    def advance(self):

        if self.simulator.proceedAndEnd == True and self.simulator.pipeline[0].instr.op == 'hlt' and self.instr.op == 'hlt':

            self.simulator.hltCount += 1
            self.simulator.dontFetch = True

            if self.simulator.hltCount == 2:
                # self.simulator.pipeline[0] = FetchStage(Nop,self.simulator)
                self.simulator.pipeline[2] = ReadStage(Nop, self.simulator)


        else:

            if (self.instr.regRead):

                if 'f' in self.instr.s1:

                    self.instr.source1RegValue = self.simulator.FPregisters[self.instr.s1]
                else:

                    self.instr.source1RegValue = self.simulator.registers[self.instr.s1]
                if (self.instr.immed and
                        # these instructions require special treatment
                        not (self.instr.op == 'bne' or self.instr.op == 'beq'
                             or self.instr.op == 'lw' or self.instr.op == 'sw')):

                    if "0x" in self.instr.immed:
                        self.instr.source2RegValue = int(self.instr.immed, 16)
                    else:
                        self.instr.source2RegValue = int(self.instr.immed)
                elif self.instr.s2:
                    if 'f' in self.instr.s1:
                        self.instr.source2RegValue = self.simulator.FPregisters[self.instr.s2]
                    else:
                        self.instr.source2RegValue = self.simulator.registers[self.instr.s2]

                if self.instr.op == 'bne':
                    if self.instr.source1RegValue != self.instr.source2RegValue:
                        self.simulator.branched = True
                    else:
                        self.simulator.proceedAndEnd = True
                        self.simulator.branched = False


                if (self.instr.s1 in self.simulator.hazardList or self.instr.s2 in self.simulator.hazardList):

                    self.simulator.hazardQueue[self.instr] = 'raw'
                    self.simulator.hazardDict[str(self.instr)] = 'raw'
                    # self.simulator.rawHaz = True




        if self.instr.op == 'j':

            if "0x" in self.instr.target:
                targetval = int(self.instr.target, 16)
            else:
                targetval = int(self.instr.target)
            self.simulator.programCounter = targetval

            self.simulator.pipeline[0] = FetchStage(Nop, self)


        if self.instr.regWrite:
            if self.instr.dest not in self.simulator.hazardList:
                self.simulator.hazardList.append(self.instr.dest)



    def __str__(self):
        return 'Read from Register'


class ExecStage(PipelineStage):
    def advance(self):

        self.delThis = []
        if self.instr is not Nop and self.instr.aluop:


            if self.instr.op == 'lw' or self.instr.op == 'l.d':

                if self.simulator.dCacheMiss == False and self.simulator.dCacheExists == True:
                    self.instr.source1RegValue = self.instr.source1RegValue + int(self.instr.immed)
                    if self.simulator.MainMemCount == 0 and self.simulator.hasLoadInMem == True:
                        self.simulator.hazardDict[self.instr] = 'struct'
                        self.simulator.loadBuffer.append(self.instr)
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)
                    if self.simulator.iCacheMiss == True and self.instr.source1RegValue not in self.simulator.dCacheDict:
                        self.simulator.loadBufferForCachePriority.append(self.instr)
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)


                else:
                    self.instr.source1RegValue = self.instr.source1RegValue + int(self.instr.immed)
                    if self.simulator.MainMemCount == 0 and self.simulator.hasLoadInMem == True:
                        self.simulator.loadBuffer.append(self.instr)
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)

                if self.simulator.dCacheMiss == True:
                    if self.instr not in self.simulator.loadBufferForDCacheWait:
                        self.simulator.loadBufferForDCacheWait.append(self.instr)
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)

                if (self.simulator.adderUnitQueue or self.simulator.addImmiUnitQueue or self.simulator.multiUnitQueue)  and self.simulator.dCacheMiss == False and self.simulator.hasLoadInMem == False and not self.simulator.pipeline[3].instr is Nop:
                    self.simulator.loadJustSteppingAside.append(self.instr)
                    self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)

            elif self.instr.op == 'sw' or self.instr.op == 's.d':
                self.instr.source2RegValue = self.instr.source2RegValue + int(self.instr.immed)
            elif self.instr.op == 'jr':
                self.simulator.programCounter = self.instr.source1RegValue
                # Set the other instructions currently in the pipeline to a Nop
                self.simulator.pipeline[0] = FetchStage(Nop, self)
                self.simulator.pipeline[2] = ReadStage(Nop, self)

            elif self.instr.op == 'beq':
                if self.instr.source1RegValue == self.instr.source2RegValue:
                    # Set the program counter to the target address
                    self.simulator.programCounter = self.simulator.programCounter + (int(self.instr.immed) * 4) - 8
                    # Set the other instructions currently in the pipeline to Nops
                    self.simulator.pipeline[0] = FetchStage(Nop, self)
                    self.simulator.pipeline[2] = ReadStage(Nop, self)
                    self.simulator.branched = True
            elif self.instr.op == 'slt':
                val = 1 if self.instr.source1RegValue < self.instr.source2RegValue else 0
                self.instr.result = val
            elif self.instr.op == 'nor':
                self.instr.result = ~(self.instr.source1RegValue | self.instr.source2RegValue)
            elif self.instr.op in self.simulator.addsubUnitaddsubUnit:


                if len(self.simulator.adderUnitQueue) < self.simulator.theAddCycles:

                    if self.instr not in self.simulator.adderUnitQueue.keys():
                        self.simulator.adderUnitQueue[self.instr] = 0
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)



                else:
                    self.simulator.adderUnitQueuebusy = True


#####################################################################################################################3
            elif self.instr.op in self.simulator.multiplicationUnit:

                if len(self.simulator.multiUnitQueue) < self.simulator.theMultiCycles:

                    if self.instr not in self.simulator.multiUnitQueue.keys():
                        self.simulator.multiUnitQueue[self.instr] = 0
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)


                else:
                    self.simulator.multiUnitQueue = True

####################################################################################################################################
            elif self.instr.op in self.simulator.addSubImmiUnit:

                if len(self.simulator.addImmiUnitQueue) == 1:
                    self.simulator.hazardDict[self.instr] = 'struct'


                if len(self.simulator.addImmiUnitQueue) < 2:

                    if self.instr not in self.simulator.addImmiUnitQueue.keys():
                        self.simulator.addImmiUnitQueue[self.instr] = 0
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)




                else:
                    self.simulator.adderUnitImmiQueuebusy = True

            elif self.instr.op in self.simulator.divisionUnit:

                if len(self.simulator.DivUnitQueue) != 1:

                    if self.instr not in self.simulator.DivUnitQueue.keys():
                        self.simulator.DivUnitQueue[self.instr] = 0
                        self.simulator.pipeline[3] = ExecStage(Nop, self.simulator)


                else:
                    self.simulator.DivUnitQueuebusy = True


        if self.simulator.loadBufferForCachePriority and self.simulator.iCacheMiss == False:
                self.simulator.pipeline[3] = ExecStage(self.simulator.loadBufferForCachePriority.pop(0), self.simulator)
        if self.simulator.loadBufferForDCacheWait and self.simulator.dCacheMiss == False:
                self.simulator.pipeline[3] = ExecStage(self.simulator.loadBufferForDCacheWait.pop(0), self.simulator)

####################################################################################################################################
        if len(self.simulator.multiUnitQueue) > 0:
            for eachKey in self.simulator.multiUnitQueue.keys():
                if self.simulator.multiUnitQueue[eachKey] == self.simulator.theMultiCycles:

                    if eachKey not in self.simulator.doneAddEx:
                        self.simulator.doneAddEx.append(eachKey)
                    if self.simulator.pipeline[3].instr is Nop:
                        self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                        if eachKey not in self.delThis:
                            self.delThis.append(eachKey)

                else:
                    self.simulator.multiUnitQueue[eachKey] += 1
                    if self.simulator.multiUnitQueue[eachKey] == self.simulator.theMultiCycles:

                        if eachKey not in self.simulator.doneMulEx:
                            self.simulator.doneMulEx.append(eachKey)
                        if self.simulator.pipeline[3].instr is Nop:
                            self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                            if eachKey not in self.delThis:
                                self.delThis.append(eachKey)

            if self.delThis:
                self.delThis[0].result = eval("%d %s %d" %
                                              (self.delThis[0].source1RegValue,
                                               self.simulator.operations[self.delThis[0].op],
                                               self.delThis[0].source2RegValue))

                del self.simulator.multiUnitQueue[self.delThis.pop(0)]

        if len(self.simulator.adderUnitQueue) > 0:
             for eachKey in self.simulator.adderUnitQueue.keys():
                 if self.simulator.adderUnitQueue[eachKey] == self.simulator.theAddCycles:

                     if eachKey not in self.simulator.doneAddEx:
                         self.simulator.doneAddEx.append(eachKey)
                     if self.simulator.pipeline[3].instr is Nop:
                         self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                         if eachKey not in self.delThis:
                             self.delThis.append(eachKey)
                 else:
                     self.simulator.adderUnitQueue[eachKey] += 1
                     if self.simulator.adderUnitQueue[eachKey] == self.simulator.theAddCycles:

                         if eachKey not in self.simulator.doneAddEx:
                             self.simulator.doneAddEx.append(eachKey)
                         if self.simulator.pipeline[3].instr is Nop:
                             self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                             if eachKey not in self.delThis:
                                 self.delThis.append(eachKey)

             if self.delThis:
                 self.delThis[0].result = eval("%d %s %d" %
                                               (self.delThis[0].source1RegValue,
                                                self.simulator.operations[self.delThis[0].op],
                                                self.delThis[0].source2RegValue))

                 del self.simulator.adderUnitQueue[self.delThis.pop(0)]

        if len(self.simulator.addImmiUnitQueue) > 0:
            for eachKey in self.simulator.addImmiUnitQueue.keys():
                if self.simulator.addImmiUnitQueue[eachKey] == 2:

                    if str(eachKey) in str(self.simulator.pipeline[1].instr):
                        continue

                    if eachKey not in self.simulator.doneAddEx:
                        self.simulator.doneAddEx.append(eachKey)

                    if self.simulator.pipeline[3].instr is Nop:
                        self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                        if eachKey not in self.delThis:
                            self.delThis.append(eachKey)
                else:
                    self.simulator.addImmiUnitQueue[eachKey] += 1
                    if self.simulator.addImmiUnitQueue[eachKey] == 2:

                        if eachKey not in self.simulator.doneAddEx and not self.simulator.doneAddEx:
                            self.simulator.doneAddEx.append(eachKey)


                        if self.simulator.pipeline[3].instr is Nop:
                            if eachKey in self.simulator.addImmiUnitQueue:
                                self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                            if eachKey not in self.delThis:
                                self.delThis.append(eachKey)
                        # elif self.simulator.pipeline[3].instr is Nop and self.simulator.pipeline[3].instr.op in self.simulator.loadStoreUnit:
                        #     self.printThisExecuteInstead.append(str(eachKey).strip())
                        elif self.simulator.pipeline[3].instr is not Nop and self.simulator.pipeline[3].instr.op in self.simulator.loadStoreUnit:
                            # self.simulator.loadJustSteppingAside.append(self.simulator.pipeline[3].instr)
                            # self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                            self.simulator.printThisInstead.append(str(eachKey).strip())

            if self.delThis:
                self.delThis[0].result = eval("%d %s %d" %
                                              (self.delThis[0].source1RegValue,
                                               self.simulator.operations[self.delThis[0].op],
                                               self.delThis[0].source2RegValue))

                del self.simulator.addImmiUnitQueue[self.delThis.pop(0)]

            if self.simulator.pipeline[3] is Nop and self.simulator.loadJustSteppingAside:
                self.simulator.pipeline[3] = ExecStage(self.simulator.loadJustSteppingAside.pop(0),self.simulator)


        if len(self.simulator.DivUnitQueue) > 0:
             for eachKey in self.simulator.DivUnitQueue.keys():
                 if self.simulator.DivUnitQueue[eachKey] == self.simulator.theDivCycles:

                     if eachKey not in self.simulator.doneDivEx:
                         self.simulator.doneDivEx.append(eachKey)
                     if self.simulator.pipeline[3].instr is Nop:
                         self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                         if eachKey not in self.delThis:
                             self.delThis.append(eachKey)
                 else:
                     self.simulator.DivUnitQueue[eachKey] += 1
                     if self.simulator.DivUnitQueue[eachKey] == self.simulator.theDivCycles:

                         if eachKey not in self.simulator.doneDivEx:
                             self.simulator.doneDivEx.append(eachKey)
                         if self.simulator.pipeline[3].instr is Nop:
                             self.simulator.pipeline[3] = ExecStage(eachKey, self.simulator)
                             if eachKey not in self.delThis:
                                 self.delThis.append(eachKey)

             if self.delThis:
                 self.delThis[0].result = eval("%d %s %d" %
                                               (self.delThis[0].source1RegValue,
                                                self.simulator.operations[self.delThis[0].op],
                                                self.delThis[0].source2RegValue))

                 del self.simulator.DivUnitQueue[self.delThis.pop(0)]


    def __str__(self):
        return 'Execute Stage\t'


class DataStage(PipelineStage):
    def advance(self):



        if self.instr.writeMem:
            self.simulator.mainmemory[self.instr.source2RegValue] = self.instr.source1RegValue
        elif self.instr.readMem and self.simulator.dCacheMiss == False:

            if 'l.d' or 'lw' in str(self.instr):

                self.simulator.MainMemCount += 1


                if self.simulator.dCacheExists == True:
                    if self.instr.source1RegValue in self.simulator.dCacheDict:

                        self.simulator.countDCacheAR += 1

                        if self.simulator.MainMemCount == 2:
                            self.instr.result = self.simulator.mainmemory[self.instr.source1RegValue]
                            self.simulator.MainMemCountFlag = True
                    else:
                        dCacheAddrCount = self.instr.source1RegValue - 4
                        for i in range(12):
                            try:
                                self.simulator.dCacheDict[dCacheAddrCount] = self.simulator.mainmemory[dCacheAddrCount]
                                dCacheAddrCount += 1
                            except KeyError:
                                dCacheAddrCount += 1
                        self.simulator.dCacheMiss = True
                        self.simulator.dCacheMissCount = 5 + 1
                else:

                    if (self.simulator.MainMemCount == 2):
                        self.instr.result = self.simulator.mainmemory[self.instr.source1RegValue]
                        self.simulator.MainMemCountFlag = True

            else:
                self.instr.result = self.simulator.mainmemory[self.instr.source1RegValue]

        if self.simulator.dCacheMissCount == 0 and self.simulator.dCacheMiss==True:
            self.simulator.dCacheMiss = False
            self.simulator.MainMemCountFlag = True
            self.instr.result = self.simulator.mainmemory[self.instr.source1RegValue]




        elif self.simulator.dCacheMiss==True:
            self.simulator.dCacheMissCount -= 1


    def __str__(self):
        return 'Main Memory'


class WriteStage(PipelineStage):
    def advance(self):


        if self.instr.regWrite:
            if self.instr.dest == 'r0':

                pass
            elif self.instr.dest:
                if 'f' in self.instr.dest:
                    self.simulator.FPregisters[self.instr.dest] = self.instr.result
                else:
                    self.simulator.registers[self.instr.dest] = self.instr.result

        self.simulator.WBBuffer = True


    def __str__(self):
        return 'Write to Register'