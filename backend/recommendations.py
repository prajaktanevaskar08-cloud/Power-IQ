"""Step 11 - rule-based recommendation engine."""


def recommend(occupancy, devices_on, energy, temperature, capacity, yesterday=None):
    recs = []
    if occupancy == 0:
        recs.append("Room is empty but electricity consumption is high. Switch off lights, fans, AC and computers, and check for devices left on.")
    elif occupancy <= 0.25 * capacity:
        recs.append(f"Only {occupancy} people are present. Switch off unused computers and lights.")
    if occupancy > 0 and devices_on > occupancy * 1.5 + 2:
        recs.append(f"{devices_on} devices are running for {occupancy} people. Turn off the unused ones.")
    if temperature >= 30 and occupancy > 0:
        recs.append("Temperature is high. Set the AC to 24-26 C and keep doors and windows closed.")
    if yesterday and energy > yesterday * 1.15:
        recs.append("Energy consumption is higher than yesterday at this hour. Check unnecessary device usage.")
    if not recs:
        recs.append("Usage is above normal for the current occupancy. Inspect high-consuming devices (AC, projectors, computers).")
    return recs
