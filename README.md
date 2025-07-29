
# MMACRAFTAI 🥊

An integrated AI-powered suite for Mixed Martial Arts (MMA) athletes and enthusiasts, providing personalized training recommendations, real-time technique feedback, and data-driven fight outcome predictions.


--- 
## 📑 Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Methodology](#project-methodology)
- [Data Sources](#data-sources)
- [Project Timeline](#project-timeline)
- [Authors](#authors)
- [Acknowledgments](#acknowledgments)


---

## 🧠 About The Project

Mixed Martial Arts (MMA) is a complex and data-rich sport. This project, **MMACRAFTAI**, harnesses the power of Data Science and Artificial Intelligence to create a unified web platform for athletes, coaches, and fans. Our goal is to bridge the gap between generic fitness apps and professional sports analytics by offering an integrated solution that provides evidence-driven training, technique correction, and competitive insights.


---

## 🚀 Key Features

The suite is built around three core modules:

### 1. 🏋️ FightFit AI (Personalized Training)
- Recommends personalized training routines based on user goals, experience level, and physical attributes.
- Uses classification algorithms like **K-Nearest Neighbors** and **Decision Trees** to match users with optimal workout plans for strength, conditioning, or weight management.

### 2. 🥋 SmartSpar (Real-time Pose Feedback)
- Utilizes a standard webcam to provide real-time feedback on striking and defensive techniques.
- Employs **MediaPipe** for accurate body landmark detection, comparing the user's form against a template library of correct MMA stances and movements.
- Helps users refine their technique and reduce the risk of injury.

### 3. 📊 FightIQ (Fight Outcome Prediction)
- Aggregates and analyzes historical fighter data to predict the outcomes of upcoming matches.
- Trains models like **Logistic Regression** and **Random Forest** on comprehensive fighter statistics (e.g., age, reach, style, win-loss records).
- Delivers winner probabilities and key performance indicators that influence the prediction.

---

## 🛠️ Tech Stack

This project is built with open-source technologies:

- **Backend & ML:** Python 3.x, Scikit-learn, Pandas  
- **Computer Vision:** OpenCV, MediaPipe  
- **Web Framework:** Streamlit  
- **Data Visualization:** Matplotlib, Seaborn

---

## ⚙️ Project Methodology

The project is developed with a modular approach, ensuring that each component can be built, tested, and refined independently before final integration.

1. **Data Collection & Preprocessing:** Gather fighter statistics, pose template data, and user information. Clean and prepare data for model training.
2. **Model Development:**
   - *FightFit AI:* Train a classifier on user data and workout plans.
   - *SmartSpar:* Develop pose comparison logic using landmark data.
   - *FightIQ:* Train a predictive model on historical fight data.
3. **Integration & UI:** Expose the backend modules through a unified and user-friendly web interface built with Streamlit.
4. **Testing & Refinement:** Conduct iterative testing with user feedback to validate performance and improve model accuracy.


---

## 📂 Data Sources

Our models are trained on a combination of publicly available and user-generated data:

* **Fighter Statistics:**
  [Kaggle UFC Dataset](https://www.kaggle.com/datasets/rajeevw/ufcdata),
  [Sherdog](https://www.sherdog.com/), [Tapology](https://www.tapology.com/), [UFCStats](http://www.ufcstats.com/)

* **Pose Templates:**
  [MMA Pose Estimation - Roboflow Universe](https://universe.roboflow.com/mma-pose-estimation)

* **User Data:**
  Demographics and fitness goals provided by users for training recommendation.

---

## 📆 Project Timeline

| Weeks | Activity                                |
| :---: | :-------------------------------------- |
|  1–2  | Requirement analysis, literature review |
|  3–4  | Acquire & preprocess datasets           |
|  5–6  | Develop Module 1 (training recommender) |
|  7–8  | Develop Module 2 (pose detection)       |
|  9–10 | Develop Module 3 (fight prediction)     |
| 11–12 | Integrate modules, build UI             |
| 13–14 | Testing, validation, user feedback      |
|   15  | Documentation, final presentation       |

---

## 👨‍💻 Authors


* **Zaid Shaikh** - [zaid83560@gmail.com](mailto:zaid83560@gmail.com)
* **Sajan Ram Patil** - [isajanpatil@gmail.com](mailto:isajanpatil@gmail.com)

---

## 🙏 Acknowledgments

We would like to extend our sincere gratitude to the following MMA practitioners and coaches for their invaluable feedback and expert guidance:

* **Shihan Sajid Rain** – Founder, Combat Martial Association India
* **Sensei Aadil Rain** – MMA Athlete, Karate Coach
* **Sensei Abhishek Kagda** – Head Coach, Cellvance Fitness Studio
* **Danish Siddique** – Kickboxing & MMA Instructor
* **MMAFI** – Mixed Martial Arts Federation of India
* **MMA Champions Club** – Mira Road


