import flet as ft
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import base64
import asyncio
import math
import random
import translates

async def main(page: ft.Page) -> None:
    page.title = 'Fluffy Roulette'
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = '#141221'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.fonts = {'PopinsRegular': 'fonts/Poppings-Reqular.ttf'}
    page.theme = ft.Theme(font_family='PopinsRegular')
    
    lang = 'en'  # Установите язык по умолчанию

    def translate(key, **kwargs):
        """Функция для получения перевода с подстановкой параметров"""
        return translates.translates.get(lang, {}).get(key, key).format(**kwargs)

    # Баланс
    balance = ft.Text(value=translate('balance-text', amount='0.00'), size=20, data=0)

    def payment_click(e) -> None:
        print(translate('submit-button-text'))

    # Кнопка платежей
    payment = ft.IconButton(ft.icons.PAYMENTS, on_click=payment_click)

    def dropdown_changed(e):
        nonlocal lang
        lang = e.control.value  # Обновляем язык
        # Обновляем все тексты на странице
        balance.value = translate('balance-text', amount='0.00')
        result_text.value = translate('result-text', color='')
        timer_text.value = translate('timer-text', seconds=30)
        deposit_button.text = translate('submit-button-text')
        bank_text.value = translate('bank-text', amount='0.00')  # Обновляем текст банка
        page.update()  # Обновляем страницу после изменений

    t = ft.Text()
    dd = ft.Dropdown(
        on_change=dropdown_changed,
        hint_text="en",
        options=[
            ft.dropdown.Option("en"),
            ft.dropdown.Option("ru"),
            ft.dropdown.Option("es"),
        ],
        width=80,
    )

    # Заголовок (Баланс и платежи)
    header = ft.Row(
        [
            balance,
            dd, 
            t
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    def create_wheel(colors_and_percentages: list[tuple[str, float]], angle: float = 0) -> str:
        """Создает изображение колеса с учетом поворота и возвращает как base64 строку"""
        percentages = [percentage for _, percentage in colors_and_percentages]
        colors = [color for color, _ in colors_and_percentages]

        fig, ax = plt.subplots()
        wedges, texts = ax.pie(percentages, colors=colors, startangle=angle + 90, counterclock=False)

        ax.set(aspect="equal")
        ax.axis('off')  # Убираем оси для более чистого вида

        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches='tight', transparent=True)
        buffer.seek(0)
        plt.close(fig)

        return base64.b64encode(buffer.read()).decode()

    # Цвета и проценты для колеса
    colors_and_percentages = [
        ("#e6b300", 10),
        ("#a89b28", 40),
        ("#d7743b", 25),
        ("#f0f1f6", 25)
    ]

    # Контейнер с изображением колеса
    wheel_image = ft.Image(src_base64=create_wheel(colors_and_percentages))

    # Контейнер для колеса, чтобы оно могло вращаться
    wheel_container = ft.Container(
        content=wheel_image,
        width=500,
        height=500,
        alignment=ft.alignment.center
    )

    # Текст для отображения выпавшего цвета
    result_text = ft.Text(value=translate('result-text', color=''), size=20)

    # Таймер
    timer_text = ft.Text(value=translate('timer-text', seconds=30), size=20)

    # Текст для отображения банка
    bank_text = ft.Text(value=translate('bank-text', amount='0.00'), size=20)

    # Функция для определения выпавшего сектора
    def get_color_by_angle(angle):
        """Определяет цвет по углу остановки колеса"""
        angle = angle % 360  # Учитываем стартовый угол 90 градусов для правильного выравнивания с сегментами
        cumulative_angle = 0

        for color, percentage in colors_and_percentages:
            sector_angle = 360 * (percentage / 100)
            if cumulative_angle <= angle < cumulative_angle + sector_angle:
                return color
            cumulative_angle += sector_angle
        return "Unknown"

    # Функция для плавного вращения колеса
    async def rotate_wheel(e):
        """Плавное вращение колеса"""
        start_angle = 0
        end_angle = random.uniform(2160, 4320)  # Вращение на 3-6 полных оборотов
        duration = 8  # Длительность анимации в секундах
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > duration:
                break

            t = elapsed / duration
            current_angle = start_angle + (end_angle - start_angle) * t * (2 - t)  # Е-кривая для плавного замедления
            wheel_image.src_base64 = create_wheel(colors_and_percentages, current_angle % 360)
            page.update()
            await asyncio.sleep(0.001)  # Обновление каждые 50 мс

        final_angle = end_angle % 360
        result_color = get_color_by_angle(final_angle)
        result_text.value = translate('result-text', color=result_color)
        page.update()

    # Таймер для отсчета
    async def countdown_timer():
        """Функция для отсчета времени"""
        seconds = 30
        while True:
            if timer_text.value == translate('timer-text', seconds=0):
                timer_text.value = translate('game-on-text')
                page.update()
                await asyncio.sleep(2)
                result_text.value = translate('result-text', color='')  # Очистка результата
                page.update()
                await rotate_wheel(None)  # Запускаем колесо после таймера
                seconds = 30
                timer_text.value = translate('timer-text', seconds=seconds)
                page.update()
            else:
                timer_text.value = translate('timer-text', seconds=seconds)
                seconds -= 1
                page.update()
                await asyncio.sleep(1)

    # Запускаем таймер
    asyncio.create_task(countdown_timer())

    # Кнопка для депозита
    deposit_button = ft.ElevatedButton(text=translate('submit-button-text'), on_click=lambda e: None)

    # Стрелка для указания на выбранный сегмент
    pointer = ft.IconButton(
        ft.icons.ARROW_DROP_DOWN,
        icon_size=40,
        icon_color="white",
        disabled=True
    )
    bottom_layout = ft.Row(
        [
            result_text,
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    timer_layout = ft.Row(
        [
            timer_text,
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    casino_icon = ft.Image(
                src="assets/img/casino3.png",
                width=40,
                height=40,
            )
    # Используем Stack для наложения стрелки на колесо
    stack = ft.Stack(
        [
            ft.Container(
                content=wheel_container,
                alignment=ft.alignment.top_center
            ),  # Колесо
            ft.Container(
                content=pointer,
                alignment=ft.alignment.top_center,
                offset=ft.Offset(0, 0.1)  # Позиционирование стрелки над колесом
            ),
            ft.Container(
                content=casino_icon,
                alignment=ft.alignment.top_center,
                offset=ft.Offset(0, 0.41)
            ),
            ft.Container(
                content=bottom_layout,
                alignment=ft.alignment.top_center,
                offset=ft.Offset(0, 0.85)
            ),
            ft.Container(
                content=timer_layout,
                alignment=ft.alignment.top_center,
                offset=ft.Offset(0, 0.95)
            )
        ],
        width=300,
        height=400  # Увеличиваем высоту для стрелки
    )

    # Размещаем элементы на странице
    layout = ft.Row(
        [
            stack,  # Колесо слева
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    def handle_dismissal(e):
        page.add()
    bs = ft.BottomSheet(
        content=ft.Container(
            padding=50,
            content=ft.Column(
                tight=True,
                controls=[
                    ft.Text(),
                    ft.TextField(label="Bet Amount"),
                    ft.ElevatedButton("Close bottom sheet", on_click=lambda _: page.close(bs)),
                ],
            ),
        ),
    )
    # Добавляем элементы на страницу
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.add(
        header,
        bank_text,
        layout,
        ft.ElevatedButton("Display bottom sheet", on_click=lambda _: page.open(bs))
        # deposit_button
    )

if __name__ == '__main__':

    ft.app(target=main)
