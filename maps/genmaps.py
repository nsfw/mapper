# generate some test maps

# RVIP map - each panel is a universe w/ zig-zag mapping
# 00 01 ............................................... 18 19 - Row 0
# 39 38 ............................................... 21 20 - Row 1
# 40 41 ............................................... 58 59 - Row 2
# 79 78 ............................................... 61 60 - Row 3
# 80 81 ............................................... 98 99 - Row 4

def genPanel(u, leftX, topY ):
    # assumes first pixel is upper left
    width = 20
    height = 5
    x = 0
    y = 0
    dir = 1
    for pix in range(100):
        print '{ "x":%d , "y":%d, "p":%d, "u":%d },' % (leftX + x, topY + y, pix, u)
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
