import random
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock


kivy.require("2.1.0")

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MainLayout, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.label_layout = BoxLayout(orientation='horizontal')
        self.labels = []

        for i in range(32):
            label = Label(text=f'Label {i + 1}')
            with label.canvas.before:
                Color(1, 1, 1, 1)
                label.rect = Rectangle(size=label.size, pos=label.pos)
            label.bind(size=self.update_rect, pos=self.update_rect)
            self.labels.append(label)
            self.label_layout.add_widget(label)

        self.add_widget(self.label_layout)

        self.change_color_button = Button(text='Change colors')
        self.change_color_button.bind(on_press=self.change_colors)
        self.add_widget(self.change_color_button)

    def update_rect(self, instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    def change_colors(self, instance):
        for label in self.labels:
            r, g, b = random.random(), random.random(), random.random()
            with label.canvas.before:
                Color(r, g, b, 1)
                label.rect = Rectangle(size=label.size, pos=label.pos)

class MyApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    MyApp().run()
