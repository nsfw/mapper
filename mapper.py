# Receive a 2D image and forward it via sACN to a light array via
# a mapping file.

# sACN groups lights in blocks by "universe". 
# When outputing, sequential lights must be output sequentially. A common
# configuraiton in LED matrices is a single "chain" of lights.

# DMX terminology:
# universe - uses a 16bit id and which holds upto 513 slots (bytes) (slots[513])
# start code - the first slot of the payload (slots[0]), for dimming this is "0"
# data - slots[1..512]

def makeWorkArray(m):
    # collect an array of work tuples (pixel, x, y) sorted by universe
    # and pixel
    def sortOrder(entry):
        # sort mapping by universe and ascending pixel numbers
        return (entry["u"], entry["p"])
    ou = 0
    work = []
    line = []
    for e in sorted(m, key=sortOrder):
        u = e["u"]
        # if universe has changed, then we have a new "line"
        if( u != ou):
            if(ou):
                work.append((ou, line))
            ou = u
            line = []
            # print "u = %d" % ( u )
        line.append((e["p"], e["x"], e["y"]))
    # add the last line
    work.append((u, line))
    # print "u = %d" % ( u )
    return work

# needs 0.2 lumos that supports unicast for unicast mode!

import lumos
acnList = {}    # for multicast
acn = None      # for unicast

def getAcn(u):
    # For multicast mode, we use on output socket per universe.
    # todo: add unicast flavor
    global acnList

    # if a single IP is set, then use that
    if(acn):
        return acn

    sock = acnList.get(u, False)
    if (not acn):
        # need to make one socket for this universe
        sock = lumos.DMXSource(u)
        acnList[u]=sock
    return sock

def sendUniverse(u, data):
    acn = getAcn(u)
    # print u,
    # print len(data)
    acn.send_data(data, universe=u)

def mapAndSendUniverse(u, m, h, w, img):
    # send the pixels of m to universe u
    # m is an array of tupples, (pixloc, x, y)
    # h(eight) and w(idth) describe img
    # pdb.set_trace()
    lastPix = m[-1][0]
    cur = 0
    data = []  #  Lumos lib will prepend startcode==0 to this array
    for p in range(lastPix+1):
        pixloc = m[cur][0]
        # fill in any 'missing' pixels
        if (p == pixloc):
            # use pixel value from image
            x = m[cur][1]
            y = m[cur][2]
            if(x <= w and y <= h):
                offset = (y*w+x)*4      # sendscreen includes alpha
            else:
                offset = 0              # use the first pixel if outside of source image
            data.append(ord(img[offset+0]))
            data.append(ord(img[offset+1]))
            data.append(ord(img[offset+2]))
            cur+=1
        else:
            # send 0 for missing pixels on string/universe
            data.append(0)
            data.append(0)
            data.append(0)
    # print u
    # print data
    sendUniverse(u, data)

###############################################################################
# entry
###############################################################################

# Forever:
#  When image buffer updated
#  for each universe - send all lights

# load mapping file
# from maps.map_twopanel import pixmap
from maps.full import pixmap
outmap = makeWorkArray(pixmap)

sawOSC = False
def sendPixMap(msg):
    global sawOSC
    if not sawOSC:
        print "hearing OSC"
    sawOSC=True

    # Sendscreen will send int:height, int:width, blob:rgba in bytes via OSC
    global last
    last = msg
    h = msg.data[0]
    w = msg.data[1]
    img = msg.data[2]

    # send each universe
    for u in outmap:
        mapAndSendUniverse(u[0], u[1], h, w, img)

def outputWorkArray(m):
    print "["
    for u in m:
        for p in u[1]:
            print "[%d, %d, %d, %d]," % (u[0], p[0], p[1], p[2])
    print "]"

import CCore
osc = CCore.CCore("osc-udp:") # default multicast address
# osc = CCore.CCore("osc-udp://192.168.2.110:9999")
osc = CCore.CCore("osc-udp://127.0.0.1:9999")
osc.subscribe("/screen", sendPixMap)

# execute this if you want unicast, otherwise we default to multicast
acn = lumos.DMXSource(ip="127.0.0.1")
