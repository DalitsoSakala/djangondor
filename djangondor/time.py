


def generate_day_interval_choices(divisions_per_hour=4):
    '''
    Generates a tuple of fixed time intervals in a day.
    Each item consists of two `str` items: `(time, time)`.
    `divisions_per_hour` determines the number of divisions
    in each hour.
    '''
    HOURS_IN_DAY = 24

    total_divisions = divisions_per_hour * HOURS_IN_DAY
    interval=60//divisions_per_hour
    result:list[tuple[str,str]] = []
    track_hour = 0
    track_minute = 0

    for _ in range(0, total_divisions):
        hour_str = f"0{track_hour}" if track_hour < 10 else f"{track_hour}"
        minute_str = f"0{track_minute}" if track_minute < 10 else f"{track_minute}"
        time = f"{hour_str}:{minute_str}"
        choice=time, time
        result.append(choice)

        track_minute += interval

        if track_minute >= 60:
            track_minute = 0
            track_hour += 1

    return tuple(result)
