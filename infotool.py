#!/usr/bin/python3
# read and modify amiga info files

import struct, png, sys, os

WB1_PALETTE = [
    (0, 85,170), (255,255,255), (0,0,34), (255,136,0),
    (102,102,102),(238,238,238),(221,119,68),(255,238,17)
]

WB2_PALETTE = [
    (170,170,170), (0,0,0), (255,255,255), (102,136,187),
    (238,68,68), (85,221,84), (0,68,221), (238,153,0)    
]
    

# custom value parsers/interpreters
def value_gadget_type(value):
    TYPES = { 1: "WBDISK",   2: "WBDRAWER",  3: "WBTOOL", 4: "WBPROJECT",
              5: "WBGARBAGE",6: "WBDEVICE",  7: "WBKICK", 8: "WBAPPICON" }

    if value in TYPES: return str(value) + " ("+TYPES[value]+")"
    return str(value) + " (Unknown type)"

def value_userdata(value):
    return str(value) + " (" + ("OS1.x" if value == 0 else "OS2.x") + ")"
    
def value_window_flag(value):
    FLAGS = {
        0x00000001: "WFLG_SIZEGADGET",	# include sizing system-gadget?
        0x00000002: "WFLG_DRAGBAR",	# include dragging system-gadget?
        0x00000004: "WFLG_DEPTHGADGET", # include depth arrangement gadget?
        0x00000008: "WFLG_CLOSEGADGET", # include close-box system-gadget?
        0x00000010: "WFLG_SIZEBRIGHT",	# size gadget uses right border
        0x00000020: "WFLG_SIZEBBOTTOM",	# size gadget uses bottom border

        # --- refresh modes -----------------------------------------------
        # combinations of the WFLG_REFRESHBITS select the refresh type
        0x000000C0: "WFLG_REFRESHBITS",
        0x00000000: "WFLG_SMART_REFRESH",
        0x00000040: "WFLG_SIMPLE_REFRESH",
        0x00000080: "WFLG_SUPER_BITMAP",
        0x000000C0: "WFLG_OTHER_REFRESH",

        0x00000100: "WFLG_BACKDROP",    # this is a backdrop window
        0x00000200: "WFLG_REPORTMOUSE",	# to hear about every mouse move
        0x00000400: "WFLG_GIMMEZEROZERO",# a GimmeZeroZero window
        0x00000800: "WFLG_BORDERLESS",	# to get a Window sans border
        0x00001000: "WFLG_ACTIVATE",	# when Window opens, it's Active

        # FLAGS SET BY INTUITION
        0x00002000: "WFLG_WINDOWACTIVE",# this window is the active one
        0x00004000: "WFLG_INREQUEST",	# this window is in request mode
        0x00008000: "WFLG_MENUSTATE",	# Window is active with Menus on

        # --- Other User Flags -------------------------------------------
        0x00010000: "WFLG_RMBTRAP",	# Catch RMB events for your own
        0x00020000: "WFLG_NOCAREREFRESH",# not to be bothered with REFRESH

        # --- Other Intuition Flags --------------------------------------
        0x01000000: "WFLG_WINDOWREFRESH",# Window is currently refreshing
        0x02000000: "WFLG_WBENCHWINDOW", # WorkBench tool ONLY Window
        0x04000000: "WFLG_WINDOWTICKED", # only one timer tick at a time

        # - V36 new Flags which the programmer may specify in NewWindow.Flags
        0x00040000: "WFLG_NW_EXTENDED",  # extension data provided
					 # see struct ExtNewWindow

        # --- V36 Flags to be set only by Intuition -------------------------
        0x08000000: "WFLG_VISITOR",	# visitor window
        0x10000000: "WFLG_ZOOMED",	# identifies "zoom state"
        0x20000000: "WFLG_HASZOOM",	# windowhas a zoom gadget
    }

    fstrs = []
    for f in FLAGS:
        if value & f:
            fstrs.append(FLAGS[f])

    return hex(value) + " ("+",".join(fstrs)+")"
    
def value_diskobject_magic(value):
    if value == 0xe310: return hex(value) + " (valid magic value)"
    return hex(value) + " (invalid magic value!!)"

def value_current_xy(value):
    if value == 0x80000000: return hex(value) + " (NO_ICON_POSITION)"
    return str(value)

# object structures

# L = unsigned long
# l = signed long
# H = unsigned short
# h = signed short
# B = unsigned byte
# b = signed byte

GADGET = [
    ("NextGadget", "L"),
    ("LeftEdge", "H"),
    ("TopEdge", "H"),
    ("Width", "H"),
    ("Height", "H"),
    ("Flags", "H"),
    ("Activation", "H"),
    ("GadgetType", "H"),
    ("GadgetRender", "L", hex),
    ("SelectRender", "L", hex),
    ("GadgetText", "L"),
    ("MutualExclude", "L"),
    ("SpecialInfo", "L"),
    ("GadgetId", "H"),
    ("UserData", "L", value_userdata)
]

# the main disk object the info file is based on
DISKOBJECT = [
    ( "Magic", "H", value_diskobject_magic),
    ( "Version", "H"),
    ( "Gadget", GADGET),
    ( "Type" ,"B", value_gadget_type),
    ( "Padding", "B"),
    ( "DefaultTool" ,"L", hex),
    ( "ToolTypes" ,"L", hex),
    ( "CurrentX" ,"L", value_current_xy),
    ( "CurrentY" ,"L", value_current_xy),
    ( "DrawerData" ,"L", hex),
    ( "Toolwindow" ,"L", hex),
    ( "StackSize" ,"L")
]

NEWWINDOW = [
    ( "LeftEdge", "h"),
    ( "TopEdge", "h"),
    ( "Width", "h"),
    ( "Height", "h"),
    ( "DetailPen", "B"),
    ( "BlockPen", "B"),
    ( "IDCMPFlags", "L", hex),
    ( "Flags", "L", value_window_flag),
    ( "FirstGadget", "L", hex),
    ( "CheckMark", "L"),
    ( "Title", "L", hex),
    ( "Screen", "L", hex),
    ( "BitMap", "L", hex),
    ( "MinWidth", "h"),
    ( "MinHeight", "h"),
    ( "MaxWidth", "H"),    # seems signed, is unsigned according to doc
    ( "MaxHeight", "H"),   # -"-
    ( "Type", "H")
]

DRAWERDATA = [
    ( "NewWindow", NEWWINDOW),
    ( "CurrentX", "l"),
    ( "CurrentY", "l")
]

# OS2.x adds two more fields which are stored seperately
# at the end of the file (after all icons and tool strings)
DRAWERDATA_EXTRA_OS2 = [
    ( "Flags", "L"),
    ( "ViewModes", "H")
]

IMAGE = [
    ( "LeftEdge", "H"),
    ( "TopEdge", "H"),
    ( "Width", "H"),
    ( "Height", "H"),
    ( "Depth", "H"),
    ( "ImageData", "L", hex),
    ( "PlanePick", "b"),
    ( "PlaneOnOff", "b"),
    ( "NextImage", "L")
]

def icon_decode(image, data, name, wbver, options):
    img, data = parse_structure(image, IMAGE, data, options)

    # calculate icon data size
    row_bytes = ((img["Width"] + 15) >> 4) << 1  # size in bytes of a row of pixel
    planesize = row_bytes * img["Height"]        # size in bytes of a plane
    picturesize = planesize * img["Depth"]

    # in theory the icon could be without actual data
    if not img["ImageData"]: return ( img, None, data )

    # check if remaining data is sufficient
    if picturesize > len(data):
        print("Insufficient icon data")
        return ( img, None, data )

    # create an empty array of appropriate size
    icon = [[0 for x in range(img["Width"])] for y in range(img["Height"])]
    for p in range(img["Depth"]):
        plane = data[planesize*p:planesize*(p+1)]
        for y in range(img["Height"]):
            line = plane[row_bytes*y:row_bytes*(y+1)]
            for x in range(img["Width"]):
                byte = line[x//8]
                if byte & (128>>(x%8)):
                    icon[y][x] = icon[y][x] | (1<<p);
                    
    # write icon as PNG
    if name and options["export"]:
        print("Exporting to",name+".png", "...")
        # map all pixels to workbench colors
        wb_icon = []
        if wbver == 1: colors_wb = WB1_PALETTE
        else:          colors_wb = WB2_PALETTE
        for y in range(img["Height"]):
            line = []
            for x in range(img["Width"]):
                line.extend(colors_wb[icon[y][x]])

            wb_icon.append(line)

        with open(name+'.png', 'wb') as f:
            w = png.Writer(img["Width"], img["Height"], greyscale=False)
            w.write(f, wb_icon)

    # return the icon and the number of bytes used
    return (img, icon, data[picturesize:])

def parse_structure(prefix, structure, data, options):
    LEN = { 'L':4, 'H':2, 'B':1, 'l':4, 'h':2, 'b':1 }
    obj = { }

    for item in structure:
        if isinstance(item[1], str) and item[1] in LEN:
            if not options["quiet"]:
                print(prefix+":"+item[0]+"=", end="")

            value = struct.unpack('>'+item[1], data[:LEN[item[1]]])[0]
            data = data[LEN[item[1]]:]

            # display value
            obj[item[0]] = value

            func = str  # default just print the value
            if len(item) >= 3: func = item[2]

            if isinstance(value, int):
                if not options["quiet"]:
                    print(func(value))
            
        else:
            obj[item[0]], data = parse_structure(prefix+":"+item[0], item[1], data, options)
                
    return ( obj, data )

# read an amiga info file
def info_read(filename, options):
    info = { }
    
    with open(filename, mode='rb') as file:
        data = file.read()

        # get base filename for PNG export
        basename = os.path.splitext(os.path.basename(filename))[0]

        # interpret start of file as diskobject
        info["DiskObject"], data = parse_structure("DiskObject", DISKOBJECT, data, options)

        # DrawerData needs to be present for WBDISK, WBDRAWER, WBGARBAGE
        if info["DiskObject"]["DrawerData"]:
            info["DrawerData"], data = parse_structure("DrawerData", DRAWERDATA, data, options)

        # check which wb version we have
        wb_ver = 1 if not info["DiskObject"]["Gadget"]["UserData"] else 2

        # main icon
        if info["DiskObject"]["Gadget"]["GadgetRender"]:
            icon0, image, data = icon_decode("Icon", data, basename, wb_ver, options)
            info["Icon"] = [ icon0, image ]

        # select icon
        if info["DiskObject"]["Gadget"]["SelectRender"]:
            icon1, image, data = icon_decode("IconSelect", data, basename+"_select", wb_ver, options)
            info["IconSelect"] = [ icon1, image ]
                
        if info["DiskObject"]["DefaultTool"]:
            strlen = struct.unpack('>L', data[:4])[0]
            str0 = data[4:4+strlen].decode("latin1").split("\x00")[0]
            if not options["quiet"]:
                print("DefaultTool=\""+str0+"\"")
            info["DefaultTool"] = str0
            data = data[4+strlen:]

        if info["DiskObject"]["ToolTypes"]:
            info["ToolTypes"] = []
            
            toollen = struct.unpack('>L', data[:4])[0]

            data = data[4:]
            toollen -= 4   # len itself counts as entry ...

            # we expect the tool len to be a multiple of four
            if toollen < 0 or toollen%4:
                print("Warning: Tool list length must be four or multiple of four!!!")

            # scan for strings
            tool = 0
            while toollen > 0:
                strlen = struct.unpack('>L', data[:4])[0]
                str0 = data[4:4+strlen].decode("latin1").split("\x00")[0]
                if not options["quiet"]:
                    print("ToolTypes["+str(tool)+"]=\""+str0+"\"")
                info["ToolTypes"].append(str0)
                data = data[4+strlen:]
                toollen -= 4
                tool += 1

        if info["DiskObject"]["Gadget"]["UserData"] and info["DiskObject"]["DrawerData"]:
            # in OS2.x there's an additional flags and viewmodes for DrawerData
            info["DrawerDataOS2"], data = parse_structure("DrawerDataOS2", DRAWERDATA_EXTRA_OS2, data, options)
            
        # check for unparsed data
        if len(data):
            print("Warning: Unparsed bytes:", len(data))
            print(data)

    return info

def write_structure(file, structure, data):
    LEN = { 'L':4, 'H':2, 'B':1, 'l':4, 'h':2, 'b':1 }

    for item in structure:
        if isinstance(item[1], str) and item[1] in LEN:
            # export regular value
            file.write(struct.pack('>'+item[1], data[item[0]]))                        
        else:
            # export sub-structure
            write_structure(file, item[1], data[item[0]])

def write_icon(file, icon):
    img, data = icon
    
    # write image header
    write_structure(file, IMAGE, img)

    # calculate icon data size
    row_bytes = ((img["Width"] + 15) >> 4) << 1  # size in bytes of a row of pixel
    planesize = row_bytes * img["Height"]        # size in bytes of a plane
    picturesize = planesize * img["Depth"]

    # write icon data itself    
    for d in range(img["Depth"]):
        for y in range(img["Height"]):
            for x in range(row_bytes):
                # assemble byte
                byte = 0
                for xi in range(8):
                    if x*8+xi < len(data[y]): di = data[y][x*8+xi]
                    else:                     di = 0
                    
                    if di & (1<<d): byte |= (0x80>>xi)
                
                file.write(bytes([byte]))

def info_write(filename, info):
    if filename and info and "DiskObject" in info:
        print("Writing", filename)
        
        with open(filename, mode='wb') as file:
            # write the disk object structure
            write_structure(file, DISKOBJECT, info["DiskObject"])

            # write the DrawerData if present
            if "DrawerData" in info:
                write_structure(file, DRAWERDATA, info["DrawerData"])
            
            # write the icons
            if "Icon"       in info: write_icon(file, info["Icon"])
            if "IconSelect" in info: write_icon(file, info["IconSelect"])

            if  info["DiskObject"]["DefaultTool"]:
                if "DefaultTool" in info:
                    s = info["DefaultTool"].encode("latin1")+b'\x00'
                    file.write(struct.pack('>L', len(s))+s)
            
            # append tooltypes
            if info["DiskObject"]["ToolTypes"]:
                if "ToolTypes" in info:
                    file.write(struct.pack('>L', (len(info["ToolTypes"])+1)*4))
                    for t in info["ToolTypes"]:                    
                        s = t.encode("latin1")+b'\x00'
                        file.write(struct.pack('>L', len(s))+s)
                
            # write OS2.x DrawerData
            if "DrawerData" in info and info["DiskObject"]["Gadget"]["UserData"]:
                if "DrawerDataOS2" in info:
                    write_structure(file, DRAWERDATA_EXTRA_OS2, info["DrawerDataOS2"])

def update_icon(image, filename):
    try:
        reader = png.Reader(filename)
        w,h,pixels,metadata = reader.read_flat()
        pixel_byte_width = 4 if metadata['alpha'] else 3
    except Exception as e:
        print(str(e))
        return False
        
    image[0]["Width"] = w
    image[0]["Height"] = h
    image[0]["Depth"] = 2

    # determine embedded bitmap size
    row_bytes = ((image[0]["Width"] + 15) >> 4) << 1  # size in bytes of a row of pixel
    planesize = row_bytes * image[0]["Height"]        # size in bytes of a plane
       
    # map all pixels to wb1 and wb2 color map
    icon_wb1 = [[0 for x in range(image[0]["Width"])] for y in range(image[0]["Height"])]
    dist_wb1 = 0
    icon_wb2 = [[0 for x in range(image[0]["Width"])] for y in range(image[0]["Height"])]
    dist_wb2 = 0
    for y in range(image[0]["Height"]):
        for x in range(image[0]["Width"]):
            pix = pixels[((y*w)+x)*pixel_byte_width:((y*w)+x+1)*pixel_byte_width]
            if len(pix) > 3: pix = pix[0:3]  # ignore any alpha

            # find closest color in wb1
            closest = -1
            distance = 100000
            for c in range(len(WB1_PALETTE)):
                d = ((WB1_PALETTE[c][0]-pix[0])*(WB1_PALETTE[c][0]-pix[0]) +
                     (WB1_PALETTE[c][1]-pix[1])*(WB1_PALETTE[c][1]-pix[1]) +
                     (WB1_PALETTE[c][2]-pix[2])*(WB1_PALETTE[c][2]-pix[2]))
                if d < distance:
                    closest = c
                    distance = d

            # set pixel and remember the worst case distance
            icon_wb1[y][x] = closest
            if distance > dist_wb1: dist_wb1 = distance

            # find closest color in wb2
            closest = -1
            distance = 100000
            for c in range(len(WB2_PALETTE)):
                d = ((WB2_PALETTE[c][0]-pix[0])*(WB2_PALETTE[c][0]-pix[0]) +
                     (WB2_PALETTE[c][1]-pix[1])*(WB2_PALETTE[c][1]-pix[1]) +
                     (WB2_PALETTE[c][2]-pix[2])*(WB2_PALETTE[c][2]-pix[2]))
                if d < distance:
                    closest = c
                    distance = d

            # set pixel and remember the worst case distance
            icon_wb2[y][x] = closest
            if distance > dist_wb2: dist_wb2 = distance

    # use bitmap with smaller error
    if dist_wb1 < dist_wb2:
        # check if any other than the first four/two colors have been used
        image[0]["Depth"] = 1
        for y in range(image[0]["Height"]):
            for x in range(image[0]["Width"]):
                if icon_wb1[y][x] > 1 and image[0]["Depth"] < 2: image[0]["Depth"] = 2
                if icon_wb1[y][x] > 3 and image[0]["Depth"] < 3: image[0]["Depth"] = 3
        
        print("ok, mapping to",image[0]["Depth"],"Workbench 1.x color bits with color offset", dist_wb1)
        if dist_wb1 > 1000: print("Warning, significant color offset")
        image[1] = icon_wb1
    else:
        image[0]["Depth"] = 1
        for y in range(image[0]["Height"]):
            for x in range(image[0]["Width"]):
                if icon_wb2[y][x] > 1 and image[0]["Depth"] < 2: image[0]["Depth"] = 2
                if icon_wb2[y][x] > 3 and image[0]["Depth"] < 3: image[0]["Depth"] = 3
        
        print("ok, mapping to",image[0]["Depth"],"Workbench 2.x color bits with color offset", dist_wb2)
        if dist_wb2 > 1000: print("Warning, significant color offset")
        image[1] = icon_wb2
        
    return True
    
def apply(info, value, root=True):
    # print("apply", value, info)

    if not "=" in value:
        print("Invalid value request")
        return False

    path, value = value.split("=", 1)

    # Icons, DefaultTool and ToolTypes are special root objects
    if root:
        # check if user tries to import a PNG image into an Icon
        if path == "Icon" or path == "IconSelect":
            if path in info:
                return update_icon(info[path], value)
            else:
                print("To be udpated is not present")
                return False
                
        # ToolTypes
        if path == "DefaultTool":
            # remove ticks if present
            if (len(value) > 1 and
                ((value[0] == '"' and value[-1] == '"') or
                 (value[0] == "'" and value[-1] == "'"))):
                value = value[1:-1]

            # trying to remove the entry?
            if value == "":
                if "DefaultTool" in info:
                    del info["DefaultTool"]
            else:            
                info["DefaultTool"] = value
            
            print("ok")
            return True
            
        # ToolTypes
        if path.startswith("ToolTypes[") and path.endswith("]"):
            try:
                # extract index
                index = int(path.split("[", 1)[1].split("]")[0])
            except:
                print("Error, unable to parse ToolTypes index")
                return False

            # remove ticks if present
            if (len(value) > 1 and
                ((value[0] == '"' and value[-1] == '"') or
                 (value[0] == "'" and value[-1] == "'"))):
                value = value[1:-1]
            
            # create ToolTypes array if needed
            if not "ToolTypes" in info: info["ToolTypes"] = [ ]
            
            if index > len(info["ToolTypes"]):
                print("Error, ToolTypes index out of range")
                return False

            # trying to remove an entry?
            if value == "":
                if index < len(info["ToolTypes"]):
                    info["ToolTypes"].pop(index)
            else:            
                if index == len(info["ToolTypes"]):
                    info["ToolTypes"].append(value)
                else:
                    info["ToolTypes"][index] = value

            print("ok")                
            return True

    # handle path if present
    if ":" in path:
        pp = path.split(":", 1)
        if not pp[0] in info:
            print("Error, invalid value path")
            return False
        else:
            # Icon and IconSelect are special as they additionally
            # contain the image data
            if pp[0] == "Icon" or pp[0] == "IconSelect":
                return apply(info[pp[0]][0], pp[1] + "=" + value, False)
            else:
                return apply(info[pp[0]], pp[1] + "=" + value, False)
    else:
        if not path in info:
            print("Error, invalid value path")
        else:
            if not isinstance(info[path], int):
                print("Error, cannot set non-value entry")
                return False
                
            if value.lower().startswith("0x"): info[path] = int(value, 16)
            else:                              info[path] = int(value)
            print("ok")

            return True

def check_structure(path, structure, data):
    # print("Checking", data)
    
    RANGES = { 'L': (0, 2**32-1), 'H': (0,2**16-1), 'B': (0,2**8-1),
               'l': (-(2**31), 2**31-1), 'h': (-(2**15),2**15-1), 'b': (-(2**7),2**7-1) }
    for item in structure:
        if isinstance(item[1], str) and item[1] in RANGES:
            # check regular value
            if ( data[item[0]] < RANGES[item[1]][0] or
                 data[item[0]] > RANGES[item[1]][1] ):
                print("Error: Value", str(data[item[0]]), "out of range for", path+":"+item[0])
                return False
        else:
            # check sub-structure
            if not check_structure(path+":"+item[0], item[1], data[item[0]]):
                return False

    return True
            
def info_check(info):
    # do all kinds of sanity checks
    if not info:
        print("No info to check")
        return False

    if not "DiskObject" in info:
        print("No DiskObject")
        return False

    if info["DiskObject"]["Magic"] != 0xe310:
        print("DiskObject:Magic is invalid")
        return False

    # check for valid values in structure 
    if not check_structure("DiskObject", DISKOBJECT, info["DiskObject"]):
        return False
    
    # check the DrawerData if present
    if "DrawerData" in info:
        if not check_structure("DrawerData", DRAWERDATA, info["DrawerData"]):
            return False
    
    if (info["DiskObject"]["Type"] == 1 or info["DiskObject"]["Type"] == 2 or info["DiskObject"]["Type"] == 5) and not "DrawerData" in info:
        print("Error: No DrawerData present although DiskObject:Type is WBDISK, WBDRAWER or WBGARBAGE")
        return False

    if (info["DiskObject"]["Type"] != 1 and info["DiskObject"]["Type"] != 2 and info["DiskObject"]["Type"] != 5) and "DrawerData" in info:
        print("Warning: DrawerData present although DiskObject:Type is neither WBDISK, WBDRAWER nor WBGARBAGE")
        
    # check the icons
    if "Icon" in info:
        if not check_structure("Icon", IMAGE, info["Icon"][0]):
            return False
                
    if "IconSelect" in info:
        if not check_structure("IconSelect", IMAGE, info["IconSelect"][0]):
            return False                

    # write OS2.x DrawerData
    if "DrawerDataOS2" in info:
        if not check_structure("DrawerDataOS2", DRAWERDATA_EXTRA_OS2, info["DrawerDataOS2"]):
            return False

    # check if OS2 drawerdata must (not) be present    
    if "DrawerData" in info and info["DiskObject"]["Gadget"]["UserData"] and not "DrawerDataOS2" in info:
        print("Error: DiskObject:Gadget:UserData indicates OS2.x, but no OS2.x DrawerData present")
        return False

    if "DrawerData" in info and not info["DiskObject"]["Gadget"]["UserData"] and "DrawerDataOS2" in info:
        print("Warning: DiskObject:Gadget:UserData indicates OS1.x, but OS2.x DrawerData is present. OS2.x DrawerData will be omitted")
        
    # check if DefaultTool is present
    if info["DiskObject"]["DefaultTool"] and not "DefaultTool" in info:
        print("Error: DiskObject:DefaultTool set, but no actual DefaultTool present")
        return False

    if not info["DiskObject"]["DefaultTool"] and "DefaultTool" in info:
        print("Warning: DiskObject:DefaultTool not set, but DefaultTool present. DefaultTool will be omitted")
    
    # check if ToolTypes are present
    if info["DiskObject"]["ToolTypes"] and not "ToolTypes" in info:
        print("Error: DiskObject:ToolTypes set, but no actual ToolTypes present")
        return False

    if not info["DiskObject"]["ToolTypes"] and "ToolTypes" in info:
        print("Warning: DiskObject:ToolTypes not set, but actual ToolTypes present. ToolTypes will be omitted")

    # Do icon checks
    if info["DiskObject"]["Gadget"]["GadgetRender"] and not "Icon" in info:
        print("Error: DiskObject:Gadget:GadgetRender set, but no actual Icon present")
        return False

    if not info["DiskObject"]["Gadget"]["GadgetRender"] and "Icon" in info:
        print("Warning: DiskObject:Gadget:GadgetRender not set, but actual Icon present. Icon will be omitted")
        
    if info["DiskObject"]["Gadget"]["SelectRender"] and not "IconSelect" in info:
        print("Error: DiskObject:Gadget:SelectRender set, but no actual IconSelect present")
        return False

    if not info["DiskObject"]["Gadget"]["SelectRender"] and "IconSelect" in info:
        print("Warning: DiskObject:Gadget:SelectRender not set, but actual IconSelec present. IconSelect will be omitted")

    # TODO: Do some icon sanity checks
    if "Icon" in info:
        # check if icon is bigger than the Gadget itself
        if info["Icon"][0]["Width"] > info["DiskObject"]["Gadget"]["Width"]:
            print("Error: Icon width exceeds DiskObject:Gadget width")
            return False
        
        if info["Icon"][0]["Height"] > info["DiskObject"]["Gadget"]["Height"]:
            print("Error: Icon height exceeds DiskObject:Gadget height")
            return False

    if "IconSelect" in info:
        # check if icon is bigger than the Gadget itself
        if info["IconSelect"][0]["Width"] > info["DiskObject"]["Gadget"]["Width"]:
            print("Error: IconSelect width exceeds DiskObject:Gadget width")
            return False
        
        if info["IconSelect"][0]["Height"] > info["DiskObject"]["Gadget"]["Height"]:
            print("Error: IconSelect height exceeds DiskObject:Gadget height")
            return False

    if "Icon" in info and "IconSelect" in info:
        if ( info["Icon"][0]["Width"] != info["IconSelect"][0]["Width"] or
             info["Icon"][0]["Height"] != info["IconSelect"][0]["Height"] ):
            print("Warning: Icon and IconSelect sizes differ")
    
    return True

def usage():
    print("Usage: infotool.py [options] <infofile> [values... <outfile>]")
    print("Options:")
    print("     -e     export the embedded icons as PNGs")
    print("     -q     quiet, don't list the info file contents")
    print("Values... is a list of key=value pairs to be modified.")
    print("        like e.g. DiskObject:Gadget:LeftEdge=100")
    print("   Special values are Icon, IconSelect, DefaultTool and ToolTypes")
    print("     - Icon and IconSelect can be used with a PNG")
    print("       file to replace the icon graphics like e.g.")
    print("       IconSelect=newicon.png")
    print("     - DefaultTool can be used to set the DefaultTool string like")
    print("       DefaultTool=\"SYS:MyTool\"")
    print("     - ToolTypes can be used to set one ToolTypes string like")
    print("       ToolTypes[10]=\"Hello World\"")
    
    sys.exit(0)

index = 1
options = { "quiet": False, "export": False }
while index < len(sys.argv) and sys.argv[index][0] == "-":
    if sys.argv[index][1:] == "e": options["export"] = True
    elif sys.argv[index][1:] == "q": options["quiet"] = True
    else:
        print("Unknown option", sys.argv[index])
        sys.exit(-1)

    index = index + 1
        
if index >= len(sys.argv):
    usage()

info = info_read(sys.argv[index], options)

if info_check(info) and len(sys.argv[index:]) >= 2:
    for m in range(len(sys.argv[index:])-2):
        print("Applying", sys.argv[index+1+m], "... ", end="")
        if not apply(info, sys.argv[index+1+m]):
            sys.exit(-1)            

    if not info_check(info):
        print("Check failed: Not saving file")
        sys.exit(-1)            
    else:
        info_write(sys.argv[-1], info)

