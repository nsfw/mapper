# generate some test maps

# RVIP map - each panel is a universe w/ zig-zag mapping
#   19 18 17 16 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01 00 - Row 0
#   20 21 ............................................... 38 39 - Row 1
#   59 58 ............................................... 41 40 - Row 2
#   60 61 ............................................... 78 79 - Row 3
#   99 98 ............................................... 81 80 - Row 4
#
# the 19th pixel is at x,y = 0,0 and the 0th pixel is at x,y = 19,0.
#

def genPanel(u, leftX, topY ):
    # assumes first pixel is upper right
    width = 20
    height = 5
    x = 19
    y = 0
    dir = -1
    for pix in range(100):
        print '{"p":%d, "x":%d , "y":%d, "u":%d },' % (pix, leftX + x, topY + y,  u)
        x+=dir
        if (x > width-1):
            dir = -1
            x=width-1
            y+=1
        if (x < 0):
            dir = 1
            x=0
            y+=1

def openMap():
    print ""
    print "pixmap = ["

def closeMap():
    print "]"
    print ""

def test2():
    genPanel(1, 0, 0)
    genPanel(2, 20, 0)

def full():
    # 4 panels of 20x5
    openMap()
    # top section
    genPanel(1,  0, 0)
    genPanel(2, 20, 0)
    genPanel(3, 40, 0)
    genPanel(4, 60, 0)
    # bottom section
    genPanel(5,  0, 5)
    genPanel(6, 20, 5)
    genPanel(7, 40, 5)
    genPanel(8, 60, 5)
    closeMap()


# 00 01 ............................................... 18 19 - Row 0
# 39 38 ............................................... 21 20 - Row 1
# 40 41 ............................................... 58 59 - Row 2
# 79 78 ............................................... 61 60 - Row 3
# 80 81 ............................................... 98 99 - Row 4
