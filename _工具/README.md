# 3D 服装重出工具（2026-11 重建）

## 通道
- duomi（主）：https://duomiapi.com/v1/images/generations —— 目前余额不足
- heju（备）：https://www.hejuapi.com/v1/images/generations —— key 在 taobao 店铺库 `ddwx_digitalavatar_provider_config` (provider_key=hejuapi)，返回 b64_json

## 脚本
- `pipe.py`：上传参考图到 CDN + 调生成接口 + 解码返回图
- `gen3d.py`：3D 上身图提示词（05 正面 / 06 背面）+ 品红抠图 + 尺寸锁定 + 锐化
- `key_magenta.py`：品红背景 despill 抠图（消除粉边）

## 待重出清单（56 套）
48,49,50,52,53,54,55, 56-67(12套), 28,35,39,42, 以及 02/03/04/17/18/19/20/21/22/23/24/25/26/27/31/33/34/37/41/43

## 单套流程
1. 05：图1=新正面2D → 图2=旧05（取姿势）→ 2048 出图
2. 06：图1=旧背面2D → 图2=旧06（取姿势）→ 2048 出图
3. key_magenta 抠图 → to_canvas 锁 2000×2000（内容 1838×1886）→ USM 锐化
4. 写入套系目录 05/06，旧图移到 _过程稿，写 meta
