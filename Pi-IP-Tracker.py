import socket, os, time
from subprocess import call

PORT=5009
sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('',PORT))
toPort=5007

def getLocalIP():
    gw = os.popen("ip -4 route show default").read().split()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((gw[2], 0))
    ipAddr = s.getsockname()[0]
    print("Local IP: ",ipAddr)
    return ipAddr;

def scanLocalNet():
    print("Commencing Arp...")
    call("sudo arp-scan --interface=eth0 --localnet >ArpOutput.txt", shell=True)
    print("Finished Arp, now logging.")
    IPlog=open("ArpOutput.txt","r")
    lines=IPlog.readlines()
    IPlog.close()
    out=list()
    for line in lines:
        if line[0:7]==IP[0:7]:
            values=line.split("\t")
            out.append(values[0]+","+values[1]+"\n")
    log=open("IpLog.txt","w")
    for line in out:
        log.write(line)
    log.close()

def refreshDevLogMacs():
    log=open("IpLog.txt","r")
    ipLog=log.readlines()
    log.close()
    log=open("DeviceLog.txt","r")
    devLog=log.readlines()
    log.close()
    for i in range(0,len(devLog)):
        dev=devLog[i].split(",")
        for ipLine in ipLog:
            ip=ipLine.split(",")
            if dev[1]==ip[0] and dev[3]!=ip[1][:-1]:
                print("Updated mac address for",dev[0])
                devLog[i]=dev[0]+','+dev[1]+','+dev[2]+','+ip[1][:-1]+','+dev[4]+','+dev[5]+','+time.strftime("%Y-%m-%d")+' '+time.strftime("%H:%M:%S") + '\n'
    log=open("DeviceLog.txt","w")
    for line in devLog:
        log.write(line)
    log.close()

def logMsg(msgType,devID,msg):
    global IP, toPort
    sendData=msgType+','+devID+','+msg
    sendThis=sendData.encode('utf-8') #Changing type
    sock.sendto(sendThis,(IP,toPort))
    print("Sent message:", sendData)

def getIpFromMac(mac):
    log=open("IpLog.txt","r")
    lines=log.readlines()
    log.close()
    outIP = ""
    for line in lines:
        logSplit=line.split(",")
        if logSplit[1][:-1]==mac:
            outIP = logSplit[0]
            break
    return outIP;

def getMacFromIp(devIP):
    log=open("IpLog.txt","r")
    lines=log.readlines()
    log.close()
    outMac = ""
    for line in lines:
        logSplit=line.split(",")
        if logSplit[0]==devIP:
            outMac = logSplit[1][:-1]
            break
    return outMac;

def isOnNetwork(mac):
    log=open("IpLog.txt","r")
    lines=log.readlines()
    log.close()
    onNet=False
    for line in lines:
        logSplit=line.split(",")
        if logSplit[1][:-1]==mac:
            onNet = True
            break
    return onNet;

#Refresh that dev log
def refreshDevLog():
    log=open("IpLog.txt","r")
    ipLog=log.readlines()
    log.close()
    log=open("DeviceLog.txt","r")
    devLog=log.readlines()
    log.close()
    devOut=list()
    cmdList=list()
    for devLine in devLog:
        dev=devLine.split(",")
        #print("New dev line: ", devLine)
        currentTime=float(time.strftime("%H"))+float(time.strftime("%M"))/60
        formattedTime=time.strftime("%Y-%m-%d")+' '+time.strftime("%H:%M:%S")
        lastUpdate=float(dev[6][11:13])+float(dev[6][14:16])/60
        readyForUpdate=currentTime-lastUpdate>0.02 #3 minutes timeout for offline devices
        #print("Time since update for",dev[0],"last updated",currentTime-lastUpdate)
        state="offline"
        for ipLine in ipLog:
            ip=ipLine.split(",")
            if dev[3]==ip[1][:-1]:
                state="online"
                break
        if state=="online":
            if dev[4]=="offline": #ie if there is a change in state from offline
                cmdList.append("LOG,"+dev[0]+",online")
                print("Prepped this message: LOG,"+dev[0]+",online")
                devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+',online,'+dev[5]+','+formattedTime+'\n')
            else:
                devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+',online,'+dev[5]+','+formattedTime+'\n')
        else: #state=="offline"
            if dev[4]=="online" and readyForUpdate:
                cmdList.append("LOG,"+dev[0]+",offline")
                print("Prepped this message: LOG,"+dev[0]+",offline")
                devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+',offline,'+dev[5]+','+formattedTime+'\n')
            else:
                devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+','+dev[4]+','+dev[5]+','+dev[6])
    if len(devOut)!=0:
        log=open("DeviceLog.txt","w")
        for line in devOut:
            log.write(line)
        log.close()
    if len(cmdList)!=0:
        for line in cmdList:
            cmd=line.split(",")
            logMsg(cmd[0],cmd[1],cmd[2])


def regMonDevs():
    log=open("MonitorMacs.txt","r")
    lines=log.readlines()
    log.close()
    for line in lines:
        logSplit=line.split(",")
        if isOnNetwork(logSplit[1]):
            logIP(logSplit[0],getIpFromMac(logSplit[1]),logSplit[2][:-1])
    

def logIP( devID, devIP, devDescriptor):
    logDev=devID + "," + devIP + "," + devDescriptor + ","+getMacFromIp(devIP)+",online,lastValue," +time.strftime("%Y-%m-%d")+" "+time.strftime("%H:%M:%S") + "\n"
    log=open("DeviceLog.txt","r") #open to read in file contents
    lines=log.readlines() #stores file to memory
    log.close
    lines.append(logDev) #adds the new line
    lines.reverse()
    out=list()
    entries=set()
    for line in lines:
        if line[:6] not in entries:
            out.append(line)
            entries.add(line[:6])
    out.reverse()
    log=open("DeviceLog.txt","w")
    for line in out:
        log.write(line)
    log.close()
    print("IP logged: " + logDev[:-1])
    return;

#Main code
IP=getLocalIP()
scanLocalNet()
regMonDevs()
time.sleep(1)
while True:
    scanLocalNet()
    refreshDevLogMacs()
    refreshDevLog()
    time.sleep(5)

