# 模型库与占位模型替换设计

## 为什么需要模型库

本项目明确承认：AI 根据平面图、照片或自然语言生成的原始三维场景，通常只能作为空间布局和对象类别的初稿。受视角、遮挡、尺度缺失、模型能力和训练数据影响，设备外观、尺寸、型号和内部结构可能不准确。

因此不要求 AI 从零生成每个高精度设备。更可靠的路线是：

```text
AI 生成空间结构和简单占位模型
                ↓
用户或 AI 从自有模型库推荐候选组件
                ↓
Web 端预览、对齐并由用户确认替换
                ↓
保留设备身份、指标绑定、告警规则和校准记录
```

AI 的职责是提出可检查的布局和候选，不把外观相似当作型号或资产身份的事实。

## 核心原则：对象不是模型

场景对象表示稳定的数字孪生实例；模型只是该实例当前使用的可替换外观：

```text
现实资产 asset_id
        ↓
场景实例 instance_id
        ↓
组件引用 component_ref
        ↓
GLB / USD / 其他三维资源
```

替换外观时必须保留：

- `instance_id` 和已经确认的 `asset_id`；
- 世界坐标、朝向和用户校准值；
- 指标、状态、告警和交互规则；
- 确认人、版本与替换历史。

第一版只实现“一实例替换为一外观组件”。把简单机柜展开成 U 位、门、服务器和传感器等复合结构属于后续能力。

## 最小模型库

初期使用静态目录和 `catalog.json` 即可，不需要数据库或资产管理后台：

```text
model-library/
├─ catalog.json
├─ racks/
│  └─ generic-42u/
│     └─ 1.0.0/
│        ├─ model.glb
│        ├─ preview.webp
│        └─ component.json
├─ cooling/
└─ sensors/
```

建议优先使用 GLB 作为 Web 参考运行时的交付格式。其他执行器可以通过相同组件清单引用 USD、FBX 或原生资产，开放协议不绑定 GLB。

`catalog.json` 只保存搜索所需的轻量索引：

```json
{
  "catalog_version": "0.1",
  "components": [
    {
      "component_id": "racks/generic-42u",
      "version": "1.0.0",
      "name": "通用 42U 机柜",
      "category": "rack",
      "model_url": "/model-library/racks/generic-42u/1.0.0/model.glb",
      "preview_url": "/model-library/racks/generic-42u/1.0.0/preview.webp",
      "dimensions_m": [0.6, 1.0, 2.0],
      "tags": ["42U", "cabinet", "generic"]
    }
  ]
}
```

每个 `component.json` 至少定义：

```json
{
  "component_schema": "0.1",
  "component_id": "racks/generic-42u",
  "version": "1.0.0",
  "category": "rack",
  "resources": {
    "web": "model.glb"
  },
  "units": "meters",
  "dimensions_m": [0.6, 1.0, 2.0],
  "origin": "bottom_center",
  "forward_axis": "-Y",
  "up_axis": "Z",
  "compatible_types": ["rack", "cabinet"],
  "license": {
    "spdx": "LicenseRef-Proprietary",
    "source": "internal-library"
  }
}
```

统一单位、原点、前向轴、上轴和包围盒是实现可靠自动对齐的必要条件。模型来源与许可也必须记录。

## 场景实例引用

AI 初稿可以使用占位组件并明确外观置信度：

```json
{
  "instance_id": "rack_b3",
  "type": "rack",
  "component_ref": "placeholder/rack@1.0.0",
  "transform": {
    "position": [1.0, -1.35, 0.0],
    "rotation_deg": [0, 0, 0],
    "scale": [1, 1, 1]
  },
  "estimated_dimensions_m": [0.8, 1.2, 2.2],
  "appearance_confidence": 0.35,
  "requires_confirmation": true
}
```

确认替换后只改变组件引用，并记录对齐决策：

```json
{
  "instance_id": "rack_b3",
  "component_ref": "racks/generic-42u@1.0.0",
  "fit_policy": "keep_component_dimensions",
  "confirmed_by": "operator",
  "confirmed_at": "2026-09-05T00:00:00Z"
}
```

## Web 端最小操作

```text
点击 AI 占位对象
→ 选择“替换外观”
→ 按对象类型自动筛选模型库
→ 查看缩略图、名称、版本和标准尺寸
→ 选择候选并在原位置预览
→ 处理尺寸差异提示
→ 确认、保存或撤销
```

实现上应保留稳定的外层实例节点，只替换其内部可视对象：

```text
rack_b3_group                 rack_b3_group
└─ placeholder_box     →      └─ generic_42u_model
```

点选、状态和业务数据绑定到 `rack_b3_group`，不能绑定到随组件替换而消失的具体 Mesh。

## 尺寸与对齐策略

当模型库标准尺寸与 AI 估算尺寸不一致时，不应静默拉伸模型。界面至少提供三种策略：

- `keep_component_dimensions`：采用组件真实尺寸，保持落地位置；
- `fit_to_placeholder`：按占位包围盒缩放，必须显式标记已缩放；
- `manual_calibration`：用户调整尺寸和位置后确认。

差异超过项目预设容差时必须提示。例如：

```text
场景估算：0.8 × 1.2 × 2.2 m
组件标准：0.6 × 1.0 × 2.0 m
差异超过容差，需要确认
```

## AI 候选推荐

AI 或规则节点通过模型库查询接口获得候选，不直接猜文件路径：

```json
{
  "type": "rack",
  "dimensions_hint_m": [0.6, 1.0, 2.0],
  "manufacturer_hint": "Huawei",
  "model_hint": "42U"
}
```

返回结果应包含匹配依据并要求确认：

```json
{
  "candidates": [
    {
      "component_ref": "racks/huawei/42u-a@1.0.0",
      "score": 0.91,
      "matched_by": ["category", "dimensions", "manufacturer"]
    },
    {
      "component_ref": "racks/generic-42u@1.0.0",
      "score": 0.76,
      "matched_by": ["category", "dimensions"]
    }
  ],
  "requires_confirmation": true
}
```

没有合适候选时继续使用占位模型，不强制匹配。

## 加载效率

第一版按以下顺序优化：

1. 首次加载组件 GLB 后按 `component_ref` 缓存；
2. 同一组件的多个实例从缓存克隆，不重复下载；
3. 只在用户预览或场景需要时加载正式模型；
4. 后续根据真实性能数据再增加网格压缩、纹理压缩、LOD 和实例化渲染。

日常选择与替换优先在 Web 端运行时完成，反馈最快。需要最终完整 GLB、高质量渲染或离线交付时，再把确认后的 `component_ref` 回灌给 Blender 或其他 3D 执行器进行烘焙导出。

## 下一版验收标准

- 占位模型可以从模型库替换并预览；
- 页面刷新后替换选择仍然存在；
- 替换前后的 `instance_id`、资产、指标和告警绑定不变；
- 尺寸或坐标系冲突会提示，不静默处理；
- 同一 GLB 在多个实例中只下载一次；
- 可以撤销替换并恢复占位外观；
- 模型文件缺失或加载失败时安全回退到占位模型。

完成这组能力后，模型库才从设计设想变成可验证的降本工具。
