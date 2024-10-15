# InfoTool - Amiga info file tool

This tool is meant to manipulate Amiga info files. It can be used
to change all values and to import and export icon graphics.

## Usage

```
Usage: infotool.py [options] <infofile> [values... <outfile>
Options:
     -e     export the embedded icons as PNGs
     -q     quiet, don't list the info file contents
Values... is a list of key=value pairs to be modified.
        like e.g. DiskObject:Gadget:LeftEdge=100
   Special values are Icon, IconSelect, DefaultTool and ToolTypes
     - Icon and IconSelect can be used with a PNG
       file to replace the icon graphics like e.g.
       IconSelect=newicon.png
     - DefaultTool can be used to set the DefaultTool string like
       DefaultTool="SYS:MyTool"
     - ToolTypes can be used to set one ToolTypes string like
       ToolTypes[10]="Hello World"
```

## Example usage

Extract the mouse pointer icon:

```
$ ./infotool.py -e ./Workbench1.3/Prefs/Pointer.info
DiskObject:Magic=0xe310 (valid magic value)
DiskObject:Version=1
DiskObject:Gadget:NextGadget=0
DiskObject:Gadget:LeftEdge=30
DiskObject:Gadget:TopEdge=43
DiskObject:Gadget:Width=44
DiskObject:Gadget:Height=23
DiskObject:Gadget:Flags=5
DiskObject:Gadget:Activation=3
DiskObject:Gadget:GadgetType=1
DiskObject:Gadget:GadgetRender=0x2123f8
DiskObject:Gadget:SelectRender=0x0
DiskObject:Gadget:GadgetText=0
DiskObject:Gadget:MutualExclude=0
DiskObject:Gadget:SpecialInfo=0
DiskObject:Gadget:GadgetId=0
DiskObject:Gadget:UserData=0 (OS1.x)
DiskObject:Type=4 (WBPROJECT)
DiskObject:Padding=8
DiskObject:DefaultTool=0x218af0
DiskObject:ToolTypes=0x20ddd0
DiskObject:CurrentX=26
DiskObject:CurrentY=32
DiskObject:DrawerData=0x0
DiskObject:Toolwindow=0x0
DiskObject:StackSize=0
Icon:LeftEdge=0
Icon:TopEdge=0
Icon:Width=44
Icon:Height=23
Icon:Depth=2
Icon:ImageData=0x1d0a0
Icon:PlanePick=3
Icon:PlaneOnOff=0
Icon:NextImage=0
Exporting to Pointer.png ...
DefaultTool="SYS:Prefs/Preferences"
ToolTypes[0]="PREFS=pointer"
```

Modify DefaultTool:

```
$ ./infotool.py ./Workbench1.3/Prefs/Pointer.info DefaultTool=SYS:MyTool Pointer.info
DiskObject:Magic=0xe310 (valid magic value)
DiskObject:Version=1
DiskObject:Gadget:NextGadget=0
DiskObject:Gadget:LeftEdge=30
DiskObject:Gadget:TopEdge=43
DiskObject:Gadget:Width=44
DiskObject:Gadget:Height=23
DiskObject:Gadget:Flags=5
DiskObject:Gadget:Activation=3
DiskObject:Gadget:GadgetType=1
DiskObject:Gadget:GadgetRender=0x2123f8
DiskObject:Gadget:SelectRender=0x0
DiskObject:Gadget:GadgetText=0
DiskObject:Gadget:MutualExclude=0
DiskObject:Gadget:SpecialInfo=0
DiskObject:Gadget:GadgetId=0
DiskObject:Gadget:UserData=0 (OS1.x)
DiskObject:Type=4 (WBPROJECT)
DiskObject:Padding=8
DiskObject:DefaultTool=0x218af0
DiskObject:ToolTypes=0x20ddd0
DiskObject:CurrentX=26
DiskObject:CurrentY=32
DiskObject:DrawerData=0x0
DiskObject:Toolwindow=0x0
DiskObject:StackSize=0
Icon:LeftEdge=0
Icon:TopEdge=0
Icon:Width=44
Icon:Height=23
Icon:Depth=2
Icon:ImageData=0x1d0a0
Icon:PlanePick=3
Icon:PlaneOnOff=0
Icon:NextImage=0
DefaultTool="SYS:Prefs/Preferences"
ToolTypes[0]="PREFS=pointer"
Applying DefaultTool=SYS:MyTool ... ok
Writing Pointer.info
```
