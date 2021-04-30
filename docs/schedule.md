# 定时任务

定时任务使用库`apscheduler`实现，对基本配置项进行封装

## 示例

```python
from botoy.schedule import scheduler

job1 = scheduler.add_job(lambda: print("我一分钟出现一次"), 'interval', minutes=1)
```

具体使用方式见:[apscheduler adding jobs](https://apscheduler.readthedocs.io/en/latest/userguide.html#adding-jobs)

## 配置

在`botoy.json`进行配置

配置项以及默认值为

```json
{
  "apscheduler_autostart": true,
  "apscheduler_log_level": 30,
  "apscheduler_config": {
    "apscheduler.timezone": "Asia/Shanghai"
  }
}
```

- apscheduler_autostart: 是否自动启动定时任务。如果不开启自动启动，则需调用模块内`start_scheduler`函数进行启动
- apscheduler_log_level: scheduler 的日志等级, WARNING = 30 INFO = 20
- apscheduler_config: apscheduler 的配置项，见[configuration_guide](https://apscheduler.readthedocs.io/en/latest/userguide.html#configuring-the-scheduler) [configuration_api](https://apscheduler.readthedocs.io/en/latest/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.configure)
