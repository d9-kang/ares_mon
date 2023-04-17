from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

from serial.tools.list_ports import comports

import ares_asio_serial

kivy.require("2.1.0")


class Model(ABC):
    """
    The Model interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the model.
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the model.
        """
        pass

    @abstractmethod
    def notify(self) -> None:
        """
        Notify all observers about an event.
        """
        pass
    
class Observer(ABC):
    """
    The Observer interface declares the update method, used by subjects.
    """

    @abstractmethod
    def update(self, subject: Model) -> None:
        """
        Receive update from subject.
        """
        pass

class AresViewModel(Model):
    """
    The Subject owns some important state and notifies observers when the state
    changes.
    """

    _state: int = None
    """
    For the sake of simplicity, the Subject's state, essential to all
    subscribers, is stored in this variable.
    """

    _observers: List[Observer] = []
    """
    List of subscribers. In real life, the list of subscribers can be stored
    more comprehensively (categorized by event type, etc.).
    """

    def attach(self, observer: Observer) -> None:
        print("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    """
    The subscription management methods.
    """

    def notify(self) -> None:
        """
        Trigger an update in each subscriber.
        """

        print("Subject: Notifying observers...")
        for observer in self._observers:
            observer.update(self)

    def some_business_logic(self) -> None:
        """
        Usually, the subscription logic is only a fraction of what a Subject can
        really do. Subjects commonly hold some important business logic, that
        triggers a notification method whenever something important is about to
        happen (or after it).
        """
        print("Something do very important ")
        self.notify()

class SerialApp(App, Observer):
    def __init__(self, view_model: AresViewModel, **kwargs):
        super().__init__(**kwargs)
        self.serial_port = None  # You can initialize your serial port here
        self.data = [0] * 4  # Initialize 4-byte data
        self.leds = []
        self.led_labels = []
        self.view_model = view_model
        self.view_model.attach(self)

    def update(self, subject: Subject) -> None:
        print("ConcreteObserverA: Reacted to the event")

    def toggle_bit(self, instance):
        bit_position = int(instance.text.split(" ")[1])
        byte_position = bit_position // 8

        if instance.state == "down":
            self.data[byte_position] |= 1 << (bit_position % 8)
        else:
            self.data[byte_position] &= ~(1 << (bit_position % 8))

    def send_data(self, instance):
        if self.serial_port:
            self.serial_port.write(bytes(self.data))  # Send the 4-byte data

         # Update the sending data text field with the data being sent
        self.send_data_input.text = ' '.join(f'{byte:02X}' for byte in self.data)
        data_received = 0b1100_1010_1010_1100_0011_0011_1111_1010
        self.update_led_colors(data_received)

        self.view_model.some_business_logic()

    def update_led_colors(self, data):
        for i in range(32):
            bit = (data >> i) & 1  # Extract the i-th bit from the received data
            led_color = self.leds[i]
            if bit:
                # If the bit is 1, set the LED color to green
                led_color.rgba = (0, 1, 0, 1)  # Green color (R: 0, G: 1, B: 0, A: 1)
            else:
                # If the bit is 0, set the LED color to red
                led_color.rgba = (1, 0, 0, 1)  # Red color (R: 1, G: 0, B: 0, A: 1)

            self.led_labels[i].canvas.ask_update()  # Request a redraw for the LED label
    
    def _update_rec(self, instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    def connect_serial(self, instance):
        try:
            self.serial_port = serial.Serial(instance.text)
            print(f"Connected to port: {instance.text}")
        except Exception as e:
            print(f"Error connecting to port {instance.text}: {e}")

    def build(self):
        # Main layout
        main_layout = BoxLayout(orientation="vertical")

        # Connect, close, and send buttons
        button_layout = BoxLayout(size_hint_y=0.2)

        # Communication port selection dropdown
        dropdown = DropDown()
        for port_info in comports():
            port_button = Button(text=port_info.device, size_hint_y=None, height=44)
            port_button.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(port_button)

        select_port_button = Button(text="Select port")
        select_port_button.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, port: setattr(select_port_button, 'text', port))
        button_layout.add_widget(select_port_button)

        # Connect, close, and send buttons
        connect_button = Button(text="Connect", on_release=lambda _: self.connect_serial(select_port_button))
        close_button = Button(text="Close")
        send_button = Button(text="Send", on_release=self.send_data)
        quit_button = Button(text="Quit", on_release=self.stop)  # Create the "Quit" button and bind it to the stop method
        button_layout.add_widget(connect_button)
        button_layout.add_widget(close_button)
        button_layout.add_widget(send_button)
        button_layout.add_widget(quit_button)
        main_layout.add_widget(button_layout)

        # 32 bit data buttons
        # Bit toggle buttons
        bit_toggle_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        bit_toggle_label = Label(text="Bit Toggle Buttons", size_hint_y=0.1)
        bit_toggle_layout.add_widget(bit_toggle_label)

        data_button_layout = GridLayout(cols=4)
        for i in range(32):
            data_button = ToggleButton(text=f"Bit {i}", on_release=self.toggle_bit)
            data_button_layout.add_widget(data_button)

        bit_toggle_layout.add_widget(data_button_layout)
        main_layout.add_widget(bit_toggle_layout)

        # LEDs for received data
        led_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        led_label = Label(text="LEDs for Received Data", size_hint_y=0.1)
        led_layout.add_widget(led_label)

        led_grid_layout = GridLayout(cols=4, padding=1, spacing=1)

        # Add LED labels and rectangles
        
        for i in range(32):
            led_box = BoxLayout()
            led_label = Label(text=f"LED {i}")
            led_box.add_widget(led_label)

            with led_label.canvas.before:
                led_color = Color(0, 1, 0, 1)  # Green color (R: 0, G: 1, B: 0, A: 1)
                led_label.rect = Rectangle(pos=led_label.pos, size=led_label.size)
            
            led_label.bind(size=self._update_rec, pos=self._update_rec)

            self.leds.append(led_color)
            self.led_labels.append(led_label)
            led_grid_layout.add_widget(led_box)

        led_layout.add_widget(led_grid_layout)
        main_layout.add_widget(led_layout)

        # Text field for sending data        # Text field for sending data
        send_data_layout = BoxLayout(size_hint_y=0.2)
        send_data_label = Label(text="Send Data:", size_hint_y=1)

        self.send_data_input = TextInput(multiline=False, readonly=True)
        send_data_layout.add_widget(send_data_label)
        send_data_layout.add_widget(self.send_data_input)
        main_layout.add_widget(send_data_layout)

        # Multi-line text field for received data
        received_data_layout = BoxLayout(size_hint_y=0.8)

        # Received data label
        self.received_data_label = Label(text="Received Data:", size_hint_y=1)


        self.received_data_input = TextInput(multiline=True, readonly=True)
        received_data_layout.add_widget(self.received_data_label)
        received_data_layout.add_widget(self.received_data_input)
        main_layout.add_widget(received_data_layout)

#        self.received_data_input.text=u''.join(f'pos is {self.led_border.pos}')

        return main_layout


if __name__ == "__main__":
    model = AresViewModel()
    app_view = SerialApp(model)

    Window.size = (800, 600)  # Set the initial window size
    app_view.run()