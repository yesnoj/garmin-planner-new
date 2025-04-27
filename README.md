# garmin-planner
Tools for importing and scheduling running training plans for your Garmin watch.

The Garmin Connect web UI is OK when you want to manage a few workout sessions, 
but when you want to manage a full training plan, it is slow and clunky.

I created this tool for my personal use because I needed a way to create training
sessions in a concise way, and be able to upload them to Garmin Connect, add them
to the training calendar and do a few operations with them.

A typical workout session will look like this:

```yaml
W03S05 Long run:
- interval: 40min @ pace2
- repeat 4:
  - interval: 15min @ 4:36
  - recovery: 3min
- cooldown: 11min @ pace1
```

Where `pace1` and `pace2` are predefined paces from the optional configuration block
at the begining of the plan file:

```yaml
config:
  paces:
    pace1: 6:00-5:07
    pace2: 5:07-4:26
    marathon: 4:40-4:35
  margins:
    faster: 0:03
    slower: 0:03
  name_prefix: '42K@3h15 '
```

Target paces and heart rates can be defined in several ways:

```yaml
config:
  heart_rates:
    max_hr: 170 # Maximum hear rate. Used to calculate most target heart rates.
    rest_hr: 45 # Resting heart rate. Used to calculate heart rate reserve (TODO).
    long_run_hr: 75-84% max_hr # HR targets based on percentages of max HR.
    lt_hr: 82-91% max_hr
    recovery_hr: 70-76% max_hr
    vo2max_hr: 93-95% max_hr
    fixed: 120 # Sample fixed heart rate. No range will be applied.
    range: 120-130 # Sample fixed range HR target.
  paces:
    marathon: 42.2km in 03:00:00
    5kpace: 5km in 19:00
    long_run: 80-85% marathon
    long_run_end: 85-90% marathon
    gen_aerobic: 80% marathon
    jog: 5:30-5:10
    strides: 3:35-3:25
  margins: # Will be added around targets with no specified range.
    faster: 0:03 # 3 seconds faster than reference pace.
    slower: 0:03 # 3 seconds slower than reference pace.
    hr_up: 5 # 5% higher than reference heart rate.
    hr_down: 5 # 5% lower than reference heart rate.
  # Prefix to add to horkout names (Advanced Marathoning plan, 18 weeks, up to 89km per week)
  name_prefix: 'AM18W89K '

# Used for testing purposes. Shows ways to indicate target paces and heart rates.
W0TS0T Test paces:
- interval: 1000m @ 04:40
- interval: 1000m @ 4:40
- interval: 1000m @ 4:4
- interval: 1000m @ 04:40-04:00
- interval: 1000m in 4min
- interval: 10km in 40:00
- interval: 42.2km in 03:00:00
- interval: 10km @ marathon
- interval: 10km @ 80% marathon
- interval: 10km @ 80-90% marathon
- interval: 10km @ long_run
- interval: 10km @ gen_aerobic
- interval: 10km @hr recovery_hr
- interval: 10km @hr 115-135
- interval: 10km @hr zone_2
```

You can also add comments that will be attached to the workout steps:

```yaml
W01S03 Hills:
- warmup: lap-button
- repeat 15:
  - interval: 20s -- Uphill on a moderate slope. Fast and relaxed, without sprinting
  - recovery: lap-button -- Recovery downhill
- cooldown: 15min @ pace1
```

And use step cempletion times instead of paces as targets:

```yaml
W02S01 Intervals:
- warmup: lap-button
- interval: 3000m in 13:48
- recovery: 120s -- Jogging
- interval: 2000m in 8:18
- recovery: 120s -- Jogging
- interval: 2000m in 8:18
- recovery: 120s -- Jogging
- interval: 1000m in 3:55
- recovery: 120s -- Jogging
- cooldown: 15min @ pace1
```

Sometimes, you need to do a workout in the abominable treadmil. I do this for hard
interval sessions where it's difficult to keep the target pace unless I am forced to.
In these cases, it is better to have a time end condition rather than a distance
end condition, because Garmin watches have a hard time estimating the distance on
a treadmill. For these cases, you can use the `--treadmill` flag to convert your
workout from distance to time end condition.

Also useful for treadmills, the tool will add in the comment of each step the target
speed in kmph by converting from pace to kmph. There are many treadmills out there
that only accept speed, and not pace.

Here is the current set of commands and options. Under the [training_plans](./training_plans)
folder there are a few sample training plans.

```
$ python3 garmin_planner.py --help
usage: garmin_planner.py [-h] [--dry-run] [--oauth-folder OAUTH_FOLDER] [--treadmill] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] {login,import,export,delete,schedule,unschedule,list,fartlek} ...

positional arguments:
  {login,import,export,delete,schedule,unschedule,list,fartlek}
                        available commands
    login               refresh or create Oauth credentials for your Garmin account
    import              import workouts
    export              export current workouts
    delete              delete workouts
    schedule            schedule workouts in a training plan. Workouts should have previously been added, and be named: [PLAN_ID] W01S01 [DESCRIPTION]
    unschedule          unschedule workouts from calendar.
    list                list scheduled workouts
    fartlek             create a random fartlek workout

options:
  -h, --help            show this help message and exit
  --dry-run             Do not modify anything, only show what would be done.
  --oauth-folder OAUTH_FOLDER
                        Folder where the Garmin oauth token is stored.
  --treadmill           Convert distance end conditions to time end conditions where possible (treadmill mode).
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        set log level
```

Sample commands:

```bash
# log into Garmin Connect 
python3 garmin_planner.py login

# log in using an alternate credentials file. This allows you to manage several
# Garmin accounts (use the --oauth-folder option)
python3 --oauth-folder ~/.garth_user2 garmin_planner.py login

# Import a training plan
python3 garmin_planner.py import --workouts-file=training_plans/marathon/10_weeks/paris/42K\@3h00.yaml

# Schedule a training plan, with a race date in mind
python3 garmin_planner.py schedule --race-day=2025-04-21 --training-plan=42K\@3h00

# Import a particular workout from other training plan, and replace it if it
# already exists. This will update the workout if it was already scheduled.
python3 garmin_planner.py --treadmill import --workouts-file=training_plans/quick_import.yaml --name-filter=W08S02 --replace

# Unschedule a plan. Workouts are not deleted.
python3 garmin_planner.py unschedule  --training-plan=42K\@3h00

# Delete workouts
python3 garmin_planner.py delete --name-filter=42K\@3h00

# Schedule a random fartlek run for tomorrow
python3 garmin_planner.py fartlek --target-pace=4:30 --duration=40:00 --schedule=tomorrow
```

You will need a python environment to run this tool. This is easy to have if you
are on a Linux or a mac. If you don't have one, you can use the Google Cloud Shell: 

[![Open this project in Cloud
Shell](http://gstatic.com/cloudssh/images/open-btn.png)](https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/apsureda/garmin-planner.git&page=editor&tutorial=tutorial.md)