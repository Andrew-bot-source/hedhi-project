from datetime import date, datetime, timedelta
import calendar
import os

import joblib
import pandas as pd

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect



from .forms import (
    RegisterForm,
    ProfileForm,
    PeriodForm,
    SymptomForm,
)

from .models import (
    CycleProfile,
    CycleRecord,
    SymptomLog,
)


# =========================================================
# LOAD MACHINE LEARNING MODEL
# =========================================================

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "models",
    "menstrual_cycle_model.pkl"
)

model = joblib.load(MODEL_PATH)


# =========================================================
# HOME
# =========================================================

def home(request):

    return render(
        request,
        "tracker/home.html"
    )

# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            CycleProfile.objects.get_or_create(
                user=user
            )

            login(request, user)

            messages.success(
                request,
                "Your account was created successfully."
            )

            return redirect("profile")

    else:

        form = RegisterForm()

    return render(
        request,
        "tracker/register.html",
        {"form": form}
    )


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile_view(request):

    profile, created = CycleProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("dashboard")

    else:

        form = ProfileForm(
            instance=profile
        )

    return render(
        request,
        "tracker/profile.html",
        {"form": form}
    )


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):

    today = date.today()

    profile, created = CycleProfile.objects.get_or_create(
        user=request.user
    )

    latest_cycle = CycleRecord.objects.filter(
        user=request.user
    ).first()

    latest_symptom = SymptomLog.objects.filter(
        user=request.user
    ).first()

    next_period = None
    days_until_next = None
    current_cycle_day = None

    fertile_start = None
    fertile_end = None
    ovulation_date = None

    advice = []

    if latest_cycle:

        if latest_cycle.predicted_next_period:

            next_period = (
                latest_cycle.predicted_next_period
            )

        else:

            cycle_length = (
                latest_cycle.predicted_cycle_length
                or profile.usual_cycle_length
                or 28
            )

            next_period = (
                latest_cycle.period_start
                + timedelta(days=cycle_length)
            )

        days_until_next = (
            next_period - today
        ).days

        if today >= latest_cycle.period_start:

            current_cycle_day = (
                today
                - latest_cycle.period_start
            ).days + 1

        ovulation_date = (
            next_period
            - timedelta(days=14)
        )

        fertile_start = (
            ovulation_date
            - timedelta(days=5)
        )

        fertile_end = (
            ovulation_date
            + timedelta(days=1)
        )


    # =====================================================
    # GENERAL PERSONALIZED GUIDANCE
    # =====================================================

    if latest_symptom:

        if latest_symptom.stress_level >= 4:

            advice.append(
                "You reported a high stress level. "
                "Consider rest, relaxation, and maintaining "
                "your normal self-care routine."
            )

        if (
            latest_symptom.sleep_hours is not None
            and latest_symptom.sleep_hours < 6
        ):

            advice.append(
                "Your recent sleep entry was below six hours. "
                "A consistent sleep routine may support "
                "general wellbeing."
            )

        if latest_symptom.cramps >= 7:

            advice.append(
                "You recorded strong cramps. If pain is severe, "
                "persistent, unusual for you, or interfering "
                "with daily activities, consider seeking "
                "medical advice."
            )

    if profile.irregular:

        advice.append(
            "You marked your cycles as irregular. "
            "Logging several cycles can help you observe "
            "your personal pattern."
        )

    if not advice:

        advice.append(
            "Keep logging your period dates and symptoms "
            "to build a clearer picture of your cycle."
        )


    # =====================================================
    # CALENDAR
    # =====================================================

    cal = calendar.Calendar(
        firstweekday=0
    )

    month_days = []

    for week in cal.monthdatescalendar(
        today.year,
        today.month
    ):

        row = []

        for day_value in week:

            day_type = ""

            if day_value == today:
                day_type = "today"

            if latest_cycle:

                period_end = (
                    latest_cycle.period_end
                    or (
                        latest_cycle.period_start
                        + timedelta(
                            days=(
                                profile.usual_period_duration
                                or 5
                            ) - 1
                        )
                    )
                )

                if (
                    latest_cycle.period_start
                    <= day_value
                    <= period_end
                ):
                    day_type = "period"

                if (
                    fertile_start
                    and fertile_end
                    and fertile_start
                    <= day_value
                    <= fertile_end
                ):
                    day_type = "fertile"

                if (
                    ovulation_date
                    and day_value == ovulation_date
                ):
                    day_type = "ovulation"

                if (
                    next_period
                    and day_value == next_period
                ):
                    day_type = "predicted"

            row.append({
                "date": day_value,
                "number": day_value.day,
                "current_month":
                    day_value.month == today.month,
                "type": day_type,
            })

        month_days.append(row)


    context = {

        "profile": profile,

        "latest_cycle": latest_cycle,

        "next_period": next_period,

        "days_until_next":
            days_until_next,

        "current_cycle_day":
            current_cycle_day,

        "fertile_start":
            fertile_start,

        "fertile_end":
            fertile_end,

        "ovulation_date":
            ovulation_date,

        "advice":
            advice,

        "calendar_weeks":
            month_days,

        "calendar_month":
            today.strftime("%B %Y"),
    }

    return render(
        request,
        "tracker/dashboard.html",
        context
    )


# =========================================================
# LOG PERIOD
# =========================================================

@login_required
def log_period(request):

    if request.method == "POST":

        form = PeriodForm(
            request.POST
        )

        if form.is_valid():

            cycle = form.save(
                commit=False
            )

            cycle.user = request.user

            today = date.today()

            if cycle.period_start > today:

                form.add_error(
                    "period_start",
                    "Period start date cannot be in the future."
                )

            elif (
                cycle.period_end
                and cycle.period_end < cycle.period_start
            ):

                form.add_error(
                    "period_end",
                    "Period end date cannot be before the start date."
                )

            else:

                previous_cycle = (
                    CycleRecord.objects
                    .filter(
                        user=request.user,
                        period_start__lt=cycle.period_start
                    )
                    .order_by("-period_start")
                    .first()
                )

                if previous_cycle:

                    cycle.cycle_length = (
                        cycle.period_start
                        - previous_cycle.period_start
                    ).days

                cycle.save()

                messages.success(
                    request,
                    "Period saved successfully."
                )

                return redirect(
                    "dashboard"
                )

    else:

        form = PeriodForm()

    return render(
        request,
        "tracker/log_period.html",
        {"form": form}
    )


# =========================================================
# LOG SYMPTOMS
# =========================================================

@login_required
def symptoms(request):

    if request.method == "POST":

        form = SymptomForm(
            request.POST
        )

        if form.is_valid():

            symptom = form.save(
                commit=False
            )

            symptom.user = request.user

            if symptom.date > date.today():

                form.add_error(
                    "date",
                    "Symptom date cannot be in the future."
                )

            else:

                symptom.save()

                messages.success(
                    request,
                    "Symptoms saved successfully."
                )

                return redirect(
                    "dashboard"
                )

    else:

        form = SymptomForm()

    return render(
        request,
        "tracker/symptoms.html",
        {"form": form}
    )


# =========================================================
# HISTORY
# =========================================================

@login_required
def history(request):

    cycles = CycleRecord.objects.filter(
        user=request.user
    )

    symptoms_list = SymptomLog.objects.filter(
        user=request.user
    )[:20]

    return render(
        request,
        "tracker/history.html",
        {
            "cycles": cycles,
            "symptoms_list":
                symptoms_list
        }
    )


# =========================================================
# ML PREDICTION
# =========================================================

@login_required
def predict_cycle(request):

    context = {
        "prediction": None,
        "errors": [],
    }

    if request.method != "POST":

        return render(
            request,
            "tracker/predict.html",
            context
        )

    errors = []

    try:

        age = int(
            request.POST.get("age", "")
        )

        cycle_length = int(
            request.POST.get(
                "cycle_length",
                ""
            )
        )

        period_duration = int(
            request.POST.get(
                "period_duration",
                ""
            )
        )

        stress_level = int(
            request.POST.get(
                "stress_level",
                ""
            )
        )

        sleep_hours = float(
            request.POST.get(
                "sleep_hours",
                ""
            )
        )

        bmi = float(
            request.POST.get(
                "bmi",
                ""
            )
        )

        irregular = int(
            request.POST.get(
                "irregular",
                ""
            )
        )

    except (TypeError, ValueError):

        errors.append(
            "Please enter valid information "
            "in every field."
        )

        context["errors"] = errors

        return render(
            request,
            "tracker/predict.html",
            context
        )


    last_period_raw = request.POST.get(
        "last_period_date",
        ""
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    if not 12 <= age <= 55:
        errors.append(
            "Age must be between 12 and 55."
        )

    if not 15 <= cycle_length <= 60:
        errors.append(
            "Cycle length must be between "
            "15 and 60 days."
        )

    if not 2 <= period_duration <= 10:
        errors.append(
            "Period duration must be between "
            "2 and 10 days."
        )

    if period_duration >= cycle_length:
        errors.append(
            "Period duration must be shorter "
            "than cycle length."
        )

    if not 1 <= stress_level <= 5:
        errors.append(
            "Stress level must be between 1 and 5."
        )

    if not 2 <= sleep_hours <= 14:
        errors.append(
            "Sleep hours are outside the "
            "supported range."
        )

    if not 12 <= bmi <= 60:
        errors.append(
            "BMI is outside the supported range."
        )

    if irregular not in [0, 1]:
        errors.append(
            "Select Regular or Irregular."
        )


    try:

        last_period_date = (
            datetime.strptime(
                last_period_raw,
                "%Y-%m-%d"
            ).date()
        )

    except ValueError:

        last_period_date = None

        errors.append(
            "Select a valid last period date."
        )


    if (
        last_period_date
        and last_period_date > date.today()
    ):

        errors.append(
            "Last period cannot start "
            "in the future."
        )


    if errors:

        context["errors"] = errors

        return render(
            request,
            "tracker/predict.html",
            context
        )


    # =====================================================
    # MODEL
    # =====================================================

    user_data = pd.DataFrame([{

        "Age": age,

        "Cycle_Length":
            cycle_length,

        "Period_Duration":
            period_duration,

        "Stress_Level":
            stress_level,

        "Sleep_Hours":
            sleep_hours,

        "BMI":
            bmi,

        "Irregular":
            irregular,
    }])


    predicted_cycle_length = int(
        round(
            model.predict(
                user_data
            )[0]
        )
    )


    next_period_date = (
        last_period_date
        + timedelta(
            days=predicted_cycle_length
        )
    )

    period_end_date = (
        last_period_date
        + timedelta(
            days=period_duration - 1
        )
    )

    next_period_end_date = (
        next_period_date
        + timedelta(
            days=period_duration - 1
        )
    )

    ovulation_date = (
        next_period_date
        - timedelta(days=14)
    )

    fertile_start_date = (
        ovulation_date
        - timedelta(days=5)
    )

    fertile_end_date = (
        ovulation_date
        + timedelta(days=1)
    )


    # =====================================================
    # SAVE PREDICTION
    # =====================================================

    cycle_record = CycleRecord.objects.create(

        user=request.user,

        period_start=
            last_period_date,

        period_end=
            period_end_date,

        cycle_length=
            cycle_length,

        predicted_cycle_length=
            predicted_cycle_length,

        predicted_next_period=
            next_period_date,

        predicted_next_period_end=
            next_period_end_date,
    )


    today = date.today()

    days_until_next_period = (
        next_period_date - today
    ).days


    if today >= last_period_date:

        current_cycle_day = (
            today
            - last_period_date
        ).days + 1

    else:

        current_cycle_day = 0


    if days_until_next_period > 0:

        notification_message = (
            f"Your next period is estimated "
            f"in {days_until_next_period} days."
        )

    elif days_until_next_period == 0:

        notification_message = (
            "Your next period is estimated "
            "to start today."
        )

    else:

        notification_message = (
            "Your estimated next-period date "
            "has passed. Update your cycle "
            "information when your period starts."
        )


    context.update({

        "prediction":
            predicted_cycle_length,

        "predicted_cycle_length":
            predicted_cycle_length,

        "last_period_date":
            last_period_date,

        "period_end_date":
            period_end_date,

        "next_period_date":
            next_period_date,

        "next_period_end_date":
            next_period_end_date,

        "ovulation_date":
            ovulation_date,

        "fertile_start_date":
            fertile_start_date,

        "fertile_end_date":
            fertile_end_date,

        "current_cycle_day":
            current_cycle_day,

        "days_until_next_period":
            days_until_next_period,

        "period_reminder_date":
            next_period_date
            - timedelta(days=3),

        "notification_message":
            notification_message,
    })


    return render(
        request,
        "tracker/predict.html",
        context
    )