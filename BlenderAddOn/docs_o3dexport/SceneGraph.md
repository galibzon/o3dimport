# Export structure
- \<ProjectRoot\>/Assets/Scenes/\<SceneName\>/
  - \<SceneName\>.sgr
  - Textures/
  - Materials/
  - Meshes/

# The SceneGraph format (*.sgr)
The whole scene is just a json file, where all objects, including the root object, are dictionaries with the following properties:
- **"name"**: The name of the object.
- **"transform"**: Parent-relative transform. When not present, it is assumed to be the identity transform.
- **"mesh"**: If present, path to the fbx/gltf asset. The path is relative to the `Meshes/` folder under the Scene Root Dir.
- **"materials"**: list of material paths, each item relates to a SlotId in the Mesh Component. Each path is relative to the  `Materials/` folder under the Scene Root Dir.
- **"children"**: If present, list of children objects.

# The "transform" Property
The "transform" property, is an **optional** dictionary that describes the object transform relative to its parent. It contains the following properties. These properties match the O3DE Transform component.
Also the values match the O3DE Convention: Z Up, Y Forward, X Right.
- **"translate"**: A 3 items list for x,y,z. Example: [3.0, 0.2, -3.4]. If not present, defaults to [0.0, 0.0, 0.0].
- **"rotate"**: A 3 items list, representing Euler angles in degrees, around each basis axis. Example: [0.0, 0.0, 180.0]. If not present, defaults to [0.0, 0.0, 0.0].
- **"scale"**: A 3 items list, representing the scale factor for each dimenstion. Example: [1.0, 2.0, 0.5]. If not present, defaults to [1.0, 1.0, 1.0].
REMARK: If the "transform" property is not present, it is assumed to be the Identity Transform.


# SceneGraph Examples
## Example 1:
A scene With One Object named "Box":
```json
{
    "name" : "Box",
    "mesh": "box.fbx",
    "materials": [
        "metallic.material"
    ]
}
```

## Example 2:
Added two children to "Box": "LeftBox" and "RightBox". All the boxes use the same `Mesh`.
```json
{
    "name" : "Box",
    "mesh": "box.fbx",
    "materials": [
        "silver.material"
    ],
    "children": [
        {
            "name" : "LeftBox",
            "mesh": "box.fbx",
            "materials": [
                "gold.material"
            ],
            "transform": {
                "translate": [-0.5, 0.0, 0.0],
                "scale": [0.5, 0.5, 0.5]
            }
        },
        {
            "name" : "RightBox",
            "mesh": "box.fbx",
            "materials": [
                "copper.material"
            ],
            "transform": {
                "translate": [1.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            }
        }
    ]
}
```
