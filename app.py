from flask import Flask, render_template, request
import requests
import math
import os
import io
import base64
import matplotlib.pyplot as plt

app = Flask(__name__)

# WeatherAPI key
API_KEY = os.getenv("WEATHER_API_KEY", "YOUR_REAL_KEY_HERE")

CITY = "Bangalore"

@app.route("/", methods=["GET", "POST"])
def home():
    bangalore_data = None
    user_data = None
    escape_v = None
    fuel_used = None
    graph_url = None
    expansion_data = None

    # ---- Get Bangalore Weather ----
    try:
        url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={CITY}&days=3&aqi=no&alerts=no"
        response = requests.get(url, timeout=5)
        data = response.json()

        if "forecast" in data:
            forecast = data["forecast"]["forecastday"]
            bangalore_data = []
            for day in forecast:
                temp = day["day"]["avgtemp_c"]
                wind = day["day"]["maxwind_kph"]
                humidity = day["day"]["avghumidity"]
                cloud = day["day"].get("daily_chance_of_rain", 0)

                if 15 <= temp <= 35 and wind < 20 and humidity < 80 and cloud < 70:
                    status = "✅ Suitable"
                else:
                    status = "❌ Not Suitable"

                bangalore_data.append({
                    "date": day["date"],
                    "condition": day["day"]["condition"]["text"],
                    "avg_temp": temp,
                    "wind": wind,
                    "humidity": humidity,
                    "status": status,
                })
    except Exception as e:
        print("Weather fetch failed:", e)

    # ---- Handle POST (both forms) ----
    if request.method == "POST":
        # Identify which form was submitted
        if "mass" in request.form:  # Launch prediction form
            temp = float(request.form.get("temp", 0))
            wind = float(request.form.get("wind", 0))
            humidity = float(request.form.get("humidity", 0))
            mass = float(request.form.get("mass", 0))
            solar_index = float(request.form.get("solar", 0))

            # --- Suitability logic ---
            reasons = []
            if temp < 15:
                reasons.append("Temperature too low")
            elif temp > 35:
                reasons.append("Temperature too high")
            if wind >= 20:
                reasons.append("Wind speed too high")
            if humidity >= 80:
                reasons.append("Humidity too high")
            if solar_index < 100:
                reasons.append("Solar radiation too low")
            elif solar_index > 300:
                reasons.append("Solar radiation too high")

            if not reasons:
                status = "✅ Suitable for Launch"
                reason_text = "All parameters within safe limits."
            else:
                status = "❌ Not Suitable for Launch"
                reason_text = ", ".join(reasons) + "."

            # --- Escape velocity (km/s) ---
            G = 6.674 * 10**-11
            M = 5.972 * 10**24
            R = 6.371 * 10**6
            v_drag = 300
            escape_v = (math.sqrt(2 * G * M / R) + v_drag) / 1000

            # --- Fuel estimation ---
            if mass == 0:
                fuel_used = 0
            else:
                k = 0.8
                fuel_used = round(k * mass * (escape_v * 1000 / 9.81), 2)

            # --- Graph generation (Rocket trajectory) ---
            if mass > 0:
                t = [i for i in range(0, 61)]  # seconds
                g = 9.81
                thrust = 1.5 * mass * g
                acc = (thrust - mass * g) / mass
                height = [0.5 * acc * (i**2) / 100 for i in t]

                plt.figure()
                plt.plot(t, height, color="#58d68d")
                plt.title("Rocket Height vs Time")
                plt.xlabel("Time (s)")
                plt.ylabel("Height (m)")
                plt.grid(True)
                buf = io.BytesIO()
                plt.savefig(buf, format="png")
                buf.seek(0)
                graph_url = base64.b64encode(buf.getvalue()).decode()
                buf.close()
                plt.close()

            user_data = {
                "temp": temp,
                "wind": wind,
                "humidity": humidity,
                "mass": mass,
                "solar": solar_index,
                "status": status,
                "reason": reason_text,
            }

        elif "material" in request.form:  # Thermal expansion form
            material = request.form.get("material")
            initial_length = float(request.form.get("initial_length", 0))
            t1 = float(request.form.get("t1", 0))
            t2 = float(request.form.get("t2", 0))

            coeffs = {
                "aluminum": 23e-6,
                "steel": 12e-6,
                "titanium": 8.6e-6,
                "carbon composite": 0.5e-6
            }

            alpha = coeffs.get(material.lower(), 23e-6)
            delta_T = t2 - t1
            delta_L = alpha * initial_length * delta_T
            new_L = initial_length + delta_L

            expansion_data = {
                "material": material.capitalize(),
                "alpha": alpha,
                "initial_length": initial_length,
                "delta_T": delta_T,
                "delta_L": round(delta_L, 6),
                "new_L": round(new_L, 6),
            }

    return render_template(
        "index.html",
        bangalore=bangalore_data,
        user_data=user_data,
        escape_v=escape_v,
        fuel_used=fuel_used,
        graph_url=graph_url,
        expansion_data=expansion_data
    )


if __name__ == "__main__":
    app.run(debug=True)



