import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Draw the main database container
db_rect = Rectangle(
    (1, 1), 10, 6, linewidth=2, edgecolor="black", facecolor="lightblue", alpha=0.3
)
ax.add_patch(db_rect)
ax.text(
    6, 7.3, "SHARED DATABASE", ha="center", va="center", fontsize=16, fontweight="bold"
)

# Draw Business A container
business_a_rect = Rectangle(
    (1.5, 4), 4, 2, linewidth=1, edgecolor="blue", facecolor="lightgreen", alpha=0.5
)
ax.add_patch(business_a_rect)
ax.text(
    3.5,
    5.7,
    "BUSINESS A",
    ha="center",
    va="center",
    fontsize=12,
    fontweight="bold",
    color="darkgreen",
)

# Draw Business B container
business_b_rect = Rectangle(
    (6.5, 4), 4, 2, linewidth=1, edgecolor="red", facecolor="lightcoral", alpha=0.5
)
ax.add_patch(business_b_rect)
ax.text(
    8.5,
    5.7,
    "BUSINESS B",
    ha="center",
    va="center",
    fontsize=12,
    fontweight="bold",
    color="darkred",
)

# Draw data tables for Business A
ax.text(
    2,
    5,
    "Products",
    ha="left",
    va="center",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white"),
)
ax.text(2, 4.5, "• Laptop ($1200)", ha="left", va="center", fontsize=8)
ax.text(2, 4.2, "• Mouse ($25)", ha="left", va="center", fontsize=8)

ax.text(
    3.5,
    5,
    "Customers",
    ha="left",
    va="center",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white"),
)
ax.text(3.5, 4.5, "• John Smith", ha="left", va="center", fontsize=8)
ax.text(3.5, 4.2, "• Jane Doe", ha="left", va="center", fontsize=8)

ax.text(
    5,
    5,
    "Sales",
    ha="left",
    va="center",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white"),
)
ax.text(5, 4.5, "• Order #001", ha="left", va="center", fontsize=8)
ax.text(5, 4.2, "• Order #002", ha="left", va="center", fontsize=8)

# Draw data tables for Business B
ax.text(
    7,
    5,
    "Products",
    ha="left",
    va="center",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white"),
)
ax.text(7, 4.5, "• Laptop ($1100)", ha="left", va="center", fontsize=8)
ax.text(7, 4.2, "• Keyboard ($75)", ha="left", va="center", fontsize=8)

ax.text(
    8.5,
    5,
    "Customers",
    ha="left",
    va="center",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white"),
)
ax.text(8.5, 4.5, "• Bob Johnson", ha="left", va="center", fontsize=8)
ax.text(8.5, 4.2, "• Alice Brown", ha="left", va="center", fontsize=8)

ax.text(
    10,
    5,
    "Sales",
    ha="left",
    va="center",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white"),
)
ax.text(10, 4.5, "• Order #101", ha="left", va="center", fontsize=8)
ax.text(10, 4.2, "• Order #102", ha="left", va="center", fontsize=8)

# Draw isolation barrier
barrier = Rectangle(
    (5.9, 4), 0.2, 2, linewidth=0, edgecolor="none", facecolor="black", alpha=0.7
)
ax.add_patch(barrier)
ax.text(
    6,
    5,
    "ISOLATION\nBARRIER",
    ha="center",
    va="center",
    fontsize=9,
    color="white",
    rotation=90,
)

# Draw user accessing system
user_circle = plt.Circle((0.5, 0.5), 0.3, color="orange", alpha=0.7)
ax.add_patch(user_circle)
ax.text(0.5, 0.5, "USER", ha="center", va="center", fontsize=8, fontweight="bold")

# Draw arrows showing data flow
ax.annotate(
    "User accesses\nBusiness A data",
    xy=(3.5, 4),
    xytext=(0.8, 0.5),
    arrowprops=dict(arrowstyle="->", color="blue", lw=1.5),
    fontsize=10,
    color="blue",
    ha="center",
)

ax.annotate(
    "User accesses\nBusiness B data",
    xy=(8.5, 4),
    xytext=(0.8, 0.5),
    arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
    fontsize=10,
    color="red",
    ha="center",
)

# Add explanation text
ax.text(
    6,
    0.5,
    "Each business sees only its own data, even though they share the same database",
    ha="center",
    va="center",
    fontsize=11,
    style="italic",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.7),
)

# Set axis properties
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.set_aspect("equal")
ax.axis("off")

# Add title
plt.title("Multi-Tenancy Database Isolation", fontsize=18, fontweight="bold", pad=20)

# Save the figure
plt.tight_layout()
plt.savefig("database_isolation_diagram.png", dpi=300, bbox_inches="tight")
plt.show()
