# Basic box

This is a deliberately small story used to prove the documentation workflow.

## 1. Start a sketch

Create a sketch and choose the XY plane.

@tool sketch.create
@click plane=XY
@screenshot sketch-open

## 2. Draw the rectangle

Choose **Center Rectangle** and click the origin for the centre.

@tool sketch.rectangle.center panel=family:Rectangle
@click sketch=0,0

Move the pointer to the second point. The next screenshot is deliberately taken
**before** the click: the Rectangle tool should still be active and the live
rectangle preview should be visible.

@hover sketch=40,30
@assert tool=sketch.rectangle.center
@screenshot rectangle-preview

Click to finish the rectangle and leave the drawing tool.

@click sketch=40,30
@key Escape
@screenshot rectangle-finished

## 3. Extrude

Finish the sketch, start Extrude and enter 20 mm.

@tool sketch.finish
@tool solid.extrude
@type "20"
@screenshot extruded-box
