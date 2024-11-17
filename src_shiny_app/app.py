from shiny.express import input, render, ui
import numpy as np
import matplotlib.pyplot as plt

MAX_VALUE = 10**5

Q = [(0, 1, -2), (-2, 1, 1), (3, -2, 3), (0, 0, -1), (-4, -4, -5)]
ui.input_text("charge_input", "Введите заряды:", value=str(Q), width="100%")
ui.help_text("Заряды вводятся в формате списка кортежей (x, y, заряд), например [(0, 1, -2), (-2, 1, 1)].")

with ui.card(full_screen=True):
    
    @render.plot
    def plot():
        try:
            user_input = input.charge_input()
            Q = eval(user_input)


            for q in Q:
                if abs(q[0]) > MAX_VALUE or abs(q[1]) > MAX_VALUE or abs(q[2]) > MAX_VALUE:
                    raise ValueError(f"Значение для зарядов или их координат превышает допустимый предел {MAX_VALUE}.")
                    return
            if not all(isinstance(q, tuple) and len(q) == 3 for q in Q):
                raise ValueError("Неверный формат заряда. Ожидается список кортежей в формате [(x, y, заряд), ...]")
                return
        except Exception as e:
            return

        x_coords = [q[0] for q in Q]
        y_coords = [q[1] for q in Q]

        padding = 1

        x1 = min(x_coords) - padding
        x2 = max(x_coords) + padding
        y1 = min(y_coords) - padding
        y2 = max(y_coords) + padding
        
        lres = 10
        
        m, n = lres * (y2 - y1), lres * (x2 - x1)
        x, y = np.linspace(x1, x2, n), np.linspace(y1, y2, m)
        x, y = np.meshgrid(x, y)
        Ex = np.zeros((m, n)) 
        Ey = np.zeros((m, n)) 

        k = 9 * 10**9
        
        for j in range(m):
            for i in range(n):
                xp, yp = x[j][i], y[j][i]
                for q in Q:
                    deltaX = xp - q[0]
                    deltaY = yp - q[1] 

                    distance = (deltaX**2 + deltaY**2)**0.5

                    E = (k * q[2]) / (distance**2)     
                    Ex[j][i] += E * (deltaX / distance)
                    Ey[j][i] += E * (deltaY / distance) 
        
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.scatter([q[0] for q in Q], [q[1] for q in Q], c='red', s=[abs(q[2])*50 for q in Q], zorder=1)
        for q in Q:
            ax.text(q[0] + 0.1, q[1] - 0.3, '{}'.format(q[2]), color='black', zorder=2)
        ax.streamplot(x, y, Ex, Ey, linewidth=1, density=1.5, zorder=0)
        ax.set_title('Симуляция электростатического поля')

        return fig
