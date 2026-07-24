# Shadowrocket 配置生成说明

本目录中的 `clash_to_shadowrocket.py` 用于把 Mihomo/Clash YAML 的分流规则转换为 Shadowrocket `.conf` 配置。

## 环境要求

- Python 3.8 或更高版本
- PyYAML

安装 PyYAML：

```powershell
python -m pip install PyYAML
```

## 生成配置

在项目根目录 `F:\tools\vps\proxy-config` 中执行：

```powershell
python shadowrocket/clash_to_shadowrocket.py local-vps.yaml shadowrocket/local-vps.conf
```

参数说明：

```text
python shadowrocket/clash_to_shadowrocket.py <Clash YAML 输入文件> <Shadowrocket CONF 输出文件>
```

例如，转换其他 Clash 配置：

```powershell
python shadowrocket/clash_to_shadowrocket.py clash/example.yaml shadowrocket/example.conf
```

成功后终端会显示：

```text
Wrote shadowrocket\local-vps.conf
```

生成的配置文件位于：

```text
shadowrocket/local-vps.conf
```

## Shadowrocket 使用方法

1. 将 `local-vps.conf` 发送到 iPhone，或通过可访问的 URL 导入 Shadowrocket。
2. 在 Shadowrocket 中添加自己的代理节点或订阅。
3. 将生成的配置设为当前配置。
4. 根据需要在策略组中选择 `PROXY`、`DIRECT` 或 `REJECT`。

源 `local-vps.yaml` 没有完整的服务器地址、UUID 等节点参数，因此生成配置中的 `[Proxy]` 为空。`PROXY` 代表在 Shadowrocket 中另外添加的节点或订阅。

## 转换内容

脚本会：

- 修复源 YAML 中 UTF-8 错误解码造成的中文及 Emoji 乱码。
- 转换代理策略组。
- 保留域名、IP、端口、GEOIP 和最终兜底规则。
- 将 `MATCH` 转换为 Shadowrocket 的 `FINAL`。
- 将常见 `GEOSITE` 和 Clash YAML 规则集替换为 Shadowrocket 可读取的远程 `.list`。
- 保留自定义金融、券商、AI 和屏蔽更新规则集。

Clash 桌面端的 `applications` 进程规则无法在 iOS 上等价使用，因此转换时会忽略该规则集。

## 修改配置后重新生成

每次修改 `local-vps.yaml` 后，重新执行：

```powershell
python shadowrocket/clash_to_shadowrocket.py local-vps.yaml shadowrocket/local-vps.conf
```

该命令会覆盖原来的 `shadowrocket/local-vps.conf`。
