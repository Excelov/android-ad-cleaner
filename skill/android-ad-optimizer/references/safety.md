# Safety Notes

## Keep

Keep chat, mail, order, logistics, payment, security, account, calendar, weather warning, system update, AI response, task completion, alarm, navigation, and media playback notifications.

## Candidate words

Candidate channel names commonly include:

```text
广告、营销、内容与营销、推荐、热点、热门、资讯、福利、活动、优惠、推广、热搜
```

These are hints, not proof. The live Android notification settings page is the final check.

## Protected words

Never select a channel when its name or ID includes:

```text
聊天、私信、消息、邮件、订单、物流、支付、交易、安全、账户、账号、日历、天气、预警、更新、升级、AI、任务、提醒、导航、音乐、播放
```

An ambiguous channel stays enabled and is reported for manual review.

## Package changes

Package suspension or disabling is a separate, explicit operation. Do not use `pm uninstall`, `pm clear`, `pm disable-user`, or `pm suspend` automatically. System packages can provide updates, security, installation, backup, account, device interconnect, or recovery services even when their names look promotional.
