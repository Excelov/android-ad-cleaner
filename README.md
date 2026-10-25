# Android Ad Optimizer Skill

一个可被 Codex、Claude Code、Cursor 等 Agent 调用的 Android 减少广告与打扰 Skill。

它通过电脑上的 `adb` 做只读检查、备份和按通知渠道的可恢复调整，重点保留：

- 聊天、邮件、订单物流、支付、账户安全
- 日历、天气预警、系统更新
- AI 回复和任务完成提醒

默认不做：

- 清除应用数据
- 修改代理或网络
- 卸载应用
- 一刀切关闭整个应用通知
- 未经确认停用系统包

## 使用

把 `skill/android-ad-optimizer` 安装到 Agent 的 skills 目录，然后使用：

```text
请使用 android-ad-optimizer，检查连接的安卓设备，先给出备份和修改计划。
```

脚本只依赖 Python 标准库和 Android SDK Platform Tools：

```powershell
python .\skill\android-ad-optimizer\scripts\android_ad_optimizer.py devices
python .\skill\android-ad-optimizer\scripts\android_ad_optimizer.py inspect
python .\skill\android-ad-optimizer\scripts\android_ad_optimizer.py backup
python .\skill\android-ad-optimizer\scripts\android_ad_optimizer.py plan
python .\skill\android-ad-optimizer\scripts\android_ad_optimizer.py apply --yes
python .\skill\android-ad-optimizer\scripts\android_ad_optimizer.py restore .\backups\<备份目录> --yes
```

`apply --yes` 只处理名称明确属于营销、推荐、热门、福利、活动、优惠或内容营销的通知渠道；聊天、订单、物流、支付、安全、天气、更新等保护词会跳过。

这是“减少广告和打扰”，不是去除所有广告。应用内信息流广告、开屏广告和账号内推荐仍可能存在。

## 目录

```text
skill/android-ad-optimizer/
  SKILL.md
  references/
    safety.md
  scripts/
    android_ad_optimizer.py
tests/
  test_android_ad_optimizer.py
```

许可证：MIT
