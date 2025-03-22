from customtkinter import CTkCanvas


class ToningCanvas(CTkCanvas):
    def __init__(
            self,
            *args,
            colours: list,
            enter_color="#ADA492",
            selected_color="#000000",
            **kwargs
    ):
        self.__colors = colours
        self.__enter_color = enter_color
        self.__selected_color = selected_color
        self.__current_color = ""
        self.__before_max_draw_id = -1
        self.__max_draw_id = -1
        super().__init__(highlightthickness=0, *args, **kwargs)
        self.__create_toning_circle()

    def config(self, *args, **kwargs):
        if "colours" in kwargs:
            raise KeyError("The colours cannot be altered since they were created.")
        if "enter_color" in kwargs:
            self.__enter_color = kwargs["enter_color"]
            kwargs.pop("enter_color")
        if "selected_color" in kwargs:
            self.__selected_color = kwargs["selected_color"]
            self.itemconfig(self.__before_max_draw_id, fill=self.__selected_color)
            kwargs.pop("selected_color")
        super().config(*args, **kwargs)

    @property
    def current_color(self):
        return self.__current_color

    def __create_highlight_circle(self, pos: int, tag_name: str):
        new_tag = f"__{tag_name}"
        self.__max_draw_id = self.create_text(
            pos, 15, text="◯", font=("Arial", 21), tags=new_tag, fill=self.__enter_color
        )
        self.tag_bind(new_tag, "<Leave>", self.__vanish_highlight_circle)
        self.tag_bind(new_tag, "<Button-1>", lambda event, colour=tag_name: self.__choose_color(colour))

    def __vanish_highlight_circle(self, _):
        if self.__max_draw_id == -1:
            return
        self.delete(self.__max_draw_id)

    def __choose_color(self, colour):
        if colour == self.current_color:
            return
        if self.__before_max_draw_id != -1:
            self.delete(self.__before_max_draw_id)
        self.__before_max_draw_id = self.__max_draw_id
        self.__current_color = colour
        self.itemconfig(self.__max_draw_id, fill=self.__selected_color)
        self.__max_draw_id = -1

    def __create_toning_circle(self):
        for i, color in enumerate(self.__colors):
            x = 15 + i * 28
            self.create_aa_circle(x, 15, 10, fill=color, tags=color)
            self.tag_bind(
                color, "<Enter>", lambda event, pos=x, colour=color: self.__create_highlight_circle(pos, colour)
            )


