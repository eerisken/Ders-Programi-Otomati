from ortools.sat.python import cp_model

def create_high_school_schedule_with_debugging():
    """
    Enhanced scheduler with unsatisfiable constraint explanation using OR-Tools assumptions (9.6+).
    """

    # Data
    classes = ['9A', '9B', '9C']
    teachers = ['Teacher A', 'Teacher B', 'Teacher C', 'Teacher D', 'Teacher E']
    subjects = [
        'Mathematics', 'Physics', 'Chemistry', 'Biology', 'History',
        'Technology', 'Music', 'Arts', 'Physical Education'
    ]
    num_days = 5
    num_hours_per_day = 7

    teacher_qualifications = {
        'Teacher A': ['Mathematics', 'Physics'],
        'Teacher B': ['Mathematics', 'Chemistry'],
        'Teacher C': ['Physics', 'Biology'],
        'Teacher D': ['History', 'Chemistry'],
        'Teacher E': ['Technology', 'Music', 'Arts', 'Physical Education']
    }

    free_days = {
        'Teacher A': [2],
        'Teacher B': [],
        'Teacher C': [0, 4],
        'Teacher D': [1],
        'Teacher E': []
    }

    desired_lectures_per_class = {
        '9A': {'Mathematics': 7, 'Physics': 6, 'Chemistry': 5, 'Biology': 3, 'History': 3,
               'Technology': 3, 'Music': 3, 'Arts': 3, 'Physical Education': 2},
        '9B': {'Mathematics': 7, 'Physics': 6, 'Chemistry': 5, 'Biology': 3, 'History': 3,
               'Technology': 3, 'Music': 3, 'Arts': 3, 'Physical Education': 2},
        '9C': {'Mathematics': 7, 'Physics': 6, 'Chemistry': 5, 'Biology': 3, 'History': 3,
               'Technology': 3, 'Music': 3, 'Arts': 3, 'Physical Education': 2},
    }

    model = cp_model.CpModel()
    schedule = {}
    assumptions = []
    assumption_map = {}

    # Variables
    for cl in classes:
        for teacher in teachers:
            for day in range(num_days):
                for hour in range(num_hours_per_day):
                    for subject in subjects:
                        schedule[(cl, teacher, day, hour, subject)] = model.NewBoolVar(
                            f'schedule_{cl}_{teacher}_{day}_{hour}_{subject}'
                        )

    # Constraint: A teacher can teach at most one class at a time
    for teacher in teachers:
        for day in range(num_days):
            for hour in range(num_hours_per_day):
                model.Add(
                    sum(schedule[(cl, teacher, day, hour, subject)]
                        for cl in classes for subject in subjects) <= 1
                )

    # Constraint: Each class has exactly one lecture per hour
    for cl in classes:
        for day in range(num_days):
            for hour in range(num_hours_per_day):
                model.Add(
                    sum(schedule[(cl, teacher, day, hour, subject)]
                        for teacher in teachers for subject in subjects) == 1
                )

    # Constraint: Teacher qualifications (with assumptions)
    for cl in classes:
        for teacher in teachers:
            for day in range(num_days):
                for hour in range(num_hours_per_day):
                    for subject in subjects:
                        if subject not in teacher_qualifications[teacher]:
                            bool_lit = model.NewBoolVar(f"unqualified_{cl}_{teacher}_{day}_{hour}_{subject}")
                            model.Add(schedule[(cl, teacher, day, hour, subject)] == 0).OnlyEnforceIf(bool_lit)
                            assumptions.append(bool_lit)
                            assumption_map[bool_lit] = f"{teacher} is not qualified to teach {subject} to {cl} on day {day}, hour {hour}"

    # Constraint: Teacher free days (with assumptions)
    for cl in classes:
        for teacher, days_off in free_days.items():
            for day in days_off:
                for hour in range(num_hours_per_day):
                    for subject in subjects:
                        bool_lit = model.NewBoolVar(f"freeday_{cl}_{teacher}_{day}_{hour}_{subject}")
                        model.Add(schedule[(cl, teacher, day, hour, subject)] == 0).OnlyEnforceIf(bool_lit)
                        assumptions.append(bool_lit)
                        assumption_map[bool_lit] = f"{teacher} is off on day {day} (class {cl}, hour {hour}, {subject})"

    # Constraint: Each class must receive the required number of lectures per subject (with assumptions)
    for cl in classes:
        for subject, num_lectures in desired_lectures_per_class[cl].items():
            bool_lit = model.NewBoolVar(f"lecture_count_{cl}_{subject}")
            total_lectures = sum(schedule[(cl, teacher, day, hour, subject)]
                                 for teacher in teachers
                                 for day in range(num_days)
                                 for hour in range(num_hours_per_day))
            model.Add(total_lectures == num_lectures).OnlyEnforceIf(bool_lit)
            assumptions.append(bool_lit)
            assumption_map[bool_lit] = f"{cl} must receive {num_lectures} hours of {subject}"

    # Register assumptions with the model
    model.AddAssumptions(assumptions)

    # Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("✅ Solution Found!")
        print("-" * 50)
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for cl in classes:
            print(f"\n======== SCHEDULE FOR {cl} ========")
            for day in range(num_days):
                print(f"--- {day_names[day]} ---")
                for hour in range(num_hours_per_day):
                    assignment_found = False
                    for teacher in teachers:
                        for subject in subjects:
                            if solver.Value(schedule[(cl, teacher, day, hour, subject)]) == 1:
                                print(f"Hour {hour + 1}: {teacher} teaches {subject}")
                                assignment_found = True
                    if not assignment_found:
                        print(f"Hour {hour + 1}: Free")
                print()
    elif status == cp_model.INFEASIBLE:
        print("❌ No feasible solution found.")
        print("🔍 Likely causes (unsatisfiable core):")
        for lit in solver.SufficientAssumptionsForInfeasibility():
            print(f"- {assumption_map.get(lit, lit.Name())}")
    else:
        print("Solver finished with status:", status)

if __name__ == '__main__':
    create_high_school_schedule_with_debugging()
