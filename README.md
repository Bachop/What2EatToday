# *What to Eat Today* 今天吃什么

基于 *Python* 开发的午餐选择程序。首次运行时需录入午餐清单，以后自动读取；支持增删选项、可选的偏好权重、每天三次重选，以及按月查看使用此程序选择下的午餐日历。

## 运行

>  截至 2026/11/03，该程序属于运行测试阶段，尚未打包整理为可执行文件。

在项目目录的 PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

安装依赖后，也可以双击 **run.bat** 启动，或使用 `python -m what2eat`。当前开发环境已创建 `.venv` 并安装运行和测试依赖。

默认数据位于系统的应用数据 `lunch.db`

可指定独立目录，便于试用、迁移或备份：

```powershell
.\.venv\Scripts\python.exe main.py --data-dir .\local-data
```

关闭程序后复制整个数据目录即可备份。SQLite 避免文本配置被意外修改，但**无法阻止拥有文件权限的人使用数据库工具修改数据**。本程序不宣称加密、防篡改或防系统时间修改；每日次数以本机日期为准。日志保存在同目录的 `application.log`。

## 使用方式

1. 首次启动时，每行输入一个午餐选项；名称不可重复，最长 40 个字符。首次设置不要求填写权重，所有选项机会均等。
2. 点击「帮我选午餐」生成当天结果，自动保存。重新打开程序会显示当天已保存的结果。
3. 首次选择之外，每天最多重选 **3 次**。第一次重选不弹窗，完成后显示剩余次数；第二、三次重选前弹窗提示，取消不消耗次数。次数不会因重启或修改清单而恢复。
4. 在「管理选项」中添加、删除；需要时进入「偏好权重…」。修改一项百分比时，其余项按原比例分配剩余权重，始终归一化为 1。可恢复均等。
5. 「午餐日历」每次只显示一个月份，可逐月切换或直接选择年月。没有记录的日期为灰色，有记录的日期按选项着色；点击日期可查看完整名称。

删除选项会保留历史记录，删除全部选项后可重新录入。重新添加同名选项视为新选项。当天已保存的午餐不会因修改清单自动替换；需要替换时使用重选。

## 随机规则与边界

详细分析、优先级和示例见 [docs/algorithm.md](docs/algorithm.md)。以下约定已经实现：

| 当前选项数 | 工作日规则 |
| --- | --- |
| 1 | 每次直接选择唯一选项 |
| 2 | 同一选项最多连续出现两个工作日，周五与下周一相邻；中间缺少选择记录会中断连续计数 |
| 3～5 | 同一选项在周一至周五内最多出现两次 |
| 大于 5 | 每周最多两次；优先未轮到的选项，再尽量避开上一工作周的结果，必要时允许回补 |

- 周末可选择、重选并记入日历，但不参与工作日次数、连续工作日和轮换统计。不考虑调休和法定节假日。
- 同一天只保存最终结果，重选过程不累计到每周次数或轮换中。
- 权重用于规则筛选后的候选集。防重复和轮换优先，因此实际长期频率可能与配置权重不同。
- 权重必须大于 0。单项时固定 100%；多个选项时单项必须小于 100%。界面编辑精度为小数点后 6 位百分比，数据库保留浮点精度，计算总和在机器精度内为 1。
- 重选在符合防重复和轮换规则的候选集中尽量换一个；只剩一项时可能再次选中它，仍消耗一次重选。
- 使用本机当前时区的日期；跨午夜会刷新界面。多程序实例通过 SQLite 事务共用当天重选次数。

新增公式：设原有 N 项，一次新增 K 项，M=N+K；原有各项乘以 N/M，新项各为 1/M。例：原有 `[0.8, 0.2]`，一次新增 3 项得到 `[0.32, 0.08, 0.2, 0.2, 0.2]`。删除后对剩余权重重新归一化，保持比例。批量输入按一次新增处理。

## 模块结构

```text
main.py                  源码启动入口
what2eat/
  app.py                 应用启动、数据路径、日志和生命周期
  models.py              数据模型、常量和业务异常
  dates.py               可复用日期计算
  weights.py             可复用权重归一化、增项和比例重分配
  colors.py              稳定的选项颜色生成
  selection.py           无界面依赖的候选筛选和加权抽样
  repository.py          SQLite 表结构、事务和查询
  service.py             校验、增删改、选择和每日次数管理
  ui/
    main_window.py       主窗口
    options.py           首次录入、选项管理、权重设置
    calendar.py          单月日历和日期详情
    common.py            通用组件和错误提示
    theme.py             统一样式
tests/                   算法、事务、并发、持久化和界面验证
```

核心算法和业务层不导入 PySide6。时间和随机源可注入，便于模拟跨日、跨周和极端偏好；UI 只调用服务层。数据库使用软删除和历史快照，避免修改清单影响过去的日历。

## 验证

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

测试包括不同选项数和随机种子的全年模拟（每天三次重选）、跨周连续限制、跨周轮换、权重公式、写入失败回滚、重启次数持久化、并发实例以及离屏 Qt 界面交互。没有安装 PySide6 时界面测试会跳过，业务测试仍可独立执行。

可生成使用独立内存数据库的界面预览，**不会修改真实午餐数据**：

```powershell
.\.venv\Scripts\python.exe -m tools.preview --output artifacts
```

## 可选：打包 Windows 桌面程序

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build]"
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name What2EatToday main.py
```

将整个 `dist\What2EatToday` 目录交给使用者，双击其中的 `What2EatToday.exe`；运行时无需单独安装 Python。上述为打包方式，当前交付以已验证的源码为主。

Qt 的应用数据目录行为参考 [QStandardPaths 官方文档](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QStandardPaths.html)。

**[README.md](#what-to-eat-today-今天吃什么)** *Written by [@Bachop](https://github.com/Bachop "@Bachop"), Formally, 3rd November 2026.
<br>Modified on 3rd November 2026.*