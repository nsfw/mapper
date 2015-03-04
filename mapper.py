# Receive a 2D image and forward it via sACN to a light array via
# a mapping file.

# sACN groups lights in blocks by "universe". 
# When outputing, sequential lights must be output sequentially. A common
# configuraiton in LED matrices is a single "chain" of lights.

# DMX terminology:
# universe - uses a 16bit id and which holds upto 513 slots (bytes) (slots[513])
# start code - the first slot of the payload (slots[0]), for dimming this is "0"
# data - slots[1..512]
import json

def writePythonFromPixmap(fname, pmap,json_meta):
    # write back to a file for verification
    with open(fname,'w') as f:
        f.write("meta = ")
        f.write(str(json_meta))
        f.write("\n")
        
        f.write("pixmap = [\n")
        for row in pmap:
            f.write("%s,\n"%str(row))
        f.write("]\n")

        
def makePixmapFromJSON(j):
    """
    json file collated by universe - smash together to resemble
    {"p":0, "x":19 , "y":0, "u":1 },
    {"p":1, "x":18 , "y":0, "u":1 },
    {"p":2, "x":17 , "y":0, "u":1 },
    where 'p' is the pixel number (0-based), 'u' is universe number (1-based)
    """
    pmap=[]
    for ustring in j["universes"].keys():
        unum=int(ustring)
        for px in j["universes"][ustring]:
            p,x,y,z=px;
            pmap.append({"p":p,"x":x,"y":y,"u":unum})
  
    return pmap
    
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


# JSON file for SendScreen etc
def outputWorkArray(m,filename="full.json"):
    doc = {
        "meta":{"image_height":0,"image_width":0, "num_universes":0},
        "universes":[]
    }
    max_x = max_y = max_uni = 0
    for u in m:
        for p in u[1]:
            max_uni = max(max_uni,u[0])
            max_x = max(max_x,p[1])
            max_y = max(max_x,p[2])
            doc["universes"].append([u[0], p[0], p[1], p[2]])
   
    doc["meta"]["num_universes"] = max_uni
    doc["meta"]["image_width"] = max_x
    doc["meta"]["image_height"] = max_y
    doc["meta"]["num_unique_pixels"] = len(doc["universes"])
    
    print "outputWorkArray to %s"%filename        
    with open(filename,"w") as f:
        json.dump(doc,f, sort_keys=True, indent=4, separators=(',', ': '))

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
    if (not sock):
        # need to make one socket for this universe
        sock = lumos.DMXSource(universe=u,name="mapper-%s"%u)
        acnList[u]=sock
    return sock

def sendUniverse(u, data):
    acn = getAcn(u)
    # print u,
    # print len(data)
    acn.send_data(data)

#scale/map x,y's from the json map (accurate-ish to pixel position)
# into the size of sendscreen which may be smaller

def _maprange( a, b, s):
    # map across ranges
    # a,b are tuples showing min,max vals for input and output
	(a1, a2), (b1, b2) = a, b
    
	return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))
    
def mapXYfromJSON(mapx,mapy, oscw,osch):
    jw = json_map["meta"]["image_width"]
    jh = json_map["meta"]["image_height"]

    osc_x = _maprange((0,jw),(0,oscw),mapx)
    osc_y = _maprange((0,jh),(0,osch),mapy)
    # print("MAP X %s %s %s = %s"%(mapx,jw,oscw,osc_x))
    # print("MAP Y %s %s %s = %s"%(mapy,jh,osch,osc_y))
    
    return osc_x,osc_y

DEBUG_OUT_OF_RANGE=10  # can use special values and look for pixels to understand why its not on   
DEBUG_MISSING=0

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
            
            # for JSON map from camera, we likely have higher xy resolution
            # than sendscreen - for now map it down to sendscreen's image size
            if(json_map is not None):
                x,y = mapXYfromJSON(x,y,w,h) 
                
            if(x <= w and y <= h):
                offset = (y*w+x)*4      # sendscreen includes alpha
                data.append(ord(img[offset+0]))
                data.append(ord(img[offset+1]))
                data.append(ord(img[offset+2]))
            else:
                print "x,y %d,%d out of SendScreen image range %d %d"%(x,y,w,h)
                 # 'off' use the first pixel if outside of source image
                data+=[DEBUG_OUT_OF_RANGE]*3
             
           
            cur+=1
        else:
            # send 0 for missing pixels on string/universe
            data+=[DEBUG_MISSING]*3
            
    # print u
    # print data
    sendUniverse(u, data)
        
###############################################################################
# entry
###############################################################################

# Forever:
#  When image buffer updated
#  for each universe - send all lights
JSON_FILE = 'mapping.json'
json_map = None
try:
    fname="./maps/%s"%JSON_FILE
    print "Try to load map from %s"%fname
    with open(fname,'r') as f:
        json_map = json.load(f)
    if json_map is not None:
        # convert json to the workarray fmt
        print "Loaded map:"
        print json_map["meta"]
        pixmap = makePixmapFromJSON(json_map)
        writePythonFromPixmap("%s_pixmap.py"%fname,pixmap,json_map["meta"])
 
        outmap = makeWorkArray(pixmap)
       
except IOError as e:
    print "Could not load JSON - use PyMaps instead"

if json_map is None:
    # load mapping file
    # from maps.map_twopanel import pixmap
    from maps.full import pixmap
    outmap = makeWorkArray(pixmap)
    outputWorkArray(outmap,"maps/full.json")
sawOSC = False
def sendPixMap(msg):
    global sawOSC
  

    # Sendscreen will send int:height, int:width, blob:rgba in bytes via OSC
    global last
    last = msg
    h = msg.data[0]
    w = msg.data[1]
    img = msg.data[2]

    if not sawOSC:
        print "hearing OSC %d x %d "%(w,h)
    sawOSC=True
    
    # send each universe
    for u in outmap:
        mapAndSendUniverse(u[0], u[1], h, w, img)

import CCore
osc = CCore.CCore("osc-udp:") # default multicast address
# osc = CCore.CCore("osc-udp://192.168.2.110:9999")
osc = CCore.CCore("osc-udp://127.0.0.1:9999")
osc.subscribe("/screen", sendPixMap)

print "Listening ... "
# execute this if you want unicast, otherwise we default to multicast
# acn = lumos.DMXSource(ip="127.0.0.1")
