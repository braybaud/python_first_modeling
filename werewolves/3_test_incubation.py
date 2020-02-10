import dtk_generic_intrahost as dgi
import dtk_nodedemog as dnd


people = []

# First, make 100 people. Half men half women, age all 20
for x in range(100):
    sex = x%2
    person = dgi.create((sex, 7300, 1.0))
    people.append(person)
    pass

# Now, touch each one with an infection before we spin time
for victim in people:
    dgi.force_infect(victim)
    pass

for x in range(25):
    for person in people:
        dgi.update(person)
        pass
    pass

incubating = 0
infected = 0
for person in people:
    if dgi.is_incubating(person):
        incubating += 1
        pass
    if dgi.is_infected(person):
        infected += 1
        pass
    pass
print(f"25 days later... incubating: {incubating}\tinfected: {infected}")

for x in range(5):
    for person in people:
        dgi.update(person)
        pass
    pass

incubating = 0
infected = 0
for person in people:
    if dgi.is_incubating(person):
        incubating += 1
        pass
    if dgi.is_infected(person):
        infected += 1
        pass
    pass
print(f"5 days later... incubating: {incubating}\tinfected: {infected}")

for x in range(5):
    for person in people:
        dgi.update(person)
        pass
    pass

incubating = 0
infected = 0
for person in people:
    if dgi.is_incubating(person):
        incubating += 1
        pass
    if dgi.is_infected(person):
        infected += 1
        pass
    pass
print(f"5 days later... incubating: {incubating}\tinfected: {infected}")
print("Okay, didn't throw an exception.")

