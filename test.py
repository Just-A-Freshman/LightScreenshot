import tkinter as tk
from tkinter import ttk

class tkinter_example(object):
    def __init__(s):
        s.win = tk.Tk()               # 创建主窗口
        s.win.title("tkinter Canvas") # 窗口标题
        s.win.withdraw()              # 隐藏窗口

        s.win.update_idletasks()      # 刷新窗口
        s.width, s.height = 600,400   #获取此时窗口大小
        s.Canvas()                    # 添加Canvas界面

        #窗口位置居中
        s.win.geometry('%dx%d+%d+%d' % (s.width, s.height, 
                      (s.win.winfo_screenwidth()  - s.width)/2,
                      (s.win.winfo_screenheight() - s.height)/2))

        s.win.resizable(0,0)     # 阻止GUI大小调整
        s.win.deiconify()        # 显示窗口
        s.win.mainloop()         # 显示主窗口

    def Canvas(s):
        #新建画布界面
        canvas = tk.Canvas(s.win, width=s.width, height=s.height, highlightthickness=0, bg='#AFEEEE')  
        canvas.grid()
        #鼠标中键滚动事件
        canvas.bind("<MouseWheel>", lambda event: print("向上滚动") if event.delta > 0 else print("向下滚动"))
        #指定tag点击事件响应
        canvas.tag_bind('other','<Button-1>', lambda event: print("tags='other'的点击响应"))

        #画一条直线提供所要绘制的直线连接的两个点坐标
        canvas.create_line(0, 30, s.width, 30, fill="#476042", dash = (4, 4))  #加了dash就是虚线，不加就是实线

        #画一个矩形,提供两个点的坐标: 第一个点为左上角坐标, 第二个点为右下角坐标, outline边框颜色，fill填充颜色
        canvas.create_rectangle(5, 5, 45, 25, outline="#476042", fill="#476042", tags = "other")

        #写文字,文字将以此坐标为中心进行绘制,也写 anchor 属性来改变文字绘制的对齐方式. 比如:anchor = 'nw'
        canvas.create_text(25, 15, text="Python", fill="#ffffff")

        #画一个椭圆，提供椭圆外切矩形两个顶点，同画矩形
        canvas.create_oval(50, 5, 100, 25, fill="#476042", tags = "other")

        #画一个正圆，提供正圆外切正方形两个顶点，同画矩形
        canvas.create_oval(105, 5, 125, 25, fill="#476042", tags = "other")

        #绘制多边形
        points1 = [130, 25, 160, 25, 145,  5]#三角形
        canvas.create_polygon(points1, outline="#ff0000", fill='#ff0000', width=1, tags = "other")
  
        #绘制图片,贴图(这里的贴图必须是 全局 或者和 mainloop在同一个函数下，否则会被清除导致不显示)
        s.image = tk.PhotoImage(file = tk.__file__.split("tkinter")[0] + 'test\\imghdrdata\\python.gif')
        canvas.create_image(180, 10, anchor = 'nw', image = s.image, tags = "other")

        #画弧线(坐标，start = 开始方向角，extent = 结束方向角)
        canvas.create_arc((200, 5, 245, 50), start = 0, extent = 120, fill = "blue", tags = "other")

        #绘制Bitmap
        bitmaps = ["error", "gray75", "gray50", "gray25", "gray12", "hourglass", "info", "questhead", "question", "warning"]
        nsteps = len(bitmaps)
        step_x = int((s.width-250) / nsteps)
        for i in range(0, nsteps):
           canvas.create_bitmap(250 + (i+1)*step_x - step_x/2,15, bitmap=bitmaps[i])

        #创建一个可在 canvas 上手动绘图的效果,通过两点画线段的方式
        draw_point = ['', '']  #用于储存拖拉鼠标时的点
        revoke     = [ ] #用于储存每次鼠标绘图操作的ID供撤销用[[...],[...],[...]]
        recover    = [ ] #用于储存每次鼠标绘图的点构成的列表供恢复
        clear      = [ ] #用于记录是否使用过清空，因为列表可变，支持全局修改，所以用列表记录
        def _canvas_draw(event):
            if not event: #松开鼠标左键时执行，清空记录点
                draw_point[:] = ['','']  #[:]只改变draw_point指向的列表的内容，不是重新赋值一个新的列表所以修改值全局通用
                return
            point = [event.x, event.y]   #此次传递的点坐标
            if draw_point==['','']:      #按下鼠标左键开始拖动时执行
                draw_point[:] = point    #保存拖动的第一个点
                if len(revoke) < len(recover):
                    recover[len(revoke):] = [] #用于使用过撤销后再绘图，清除撤销点后的恢复数据
                clear[:] = []
                revoke.append([])        #新建一个撤销记录列表
                recover.append([])       #新建一个恢复记录列表
                recover[-1].extend(point)#在新建的恢复记录列表里记录第一个点
            else:
                revoke[-1].append(
                    canvas.create_line(draw_point[0], draw_point[1], event.x, event.y, fill="#476042", width=1,
                    tags = "line")
                          )      #绘制的线段并保存到撤销记录的末次列表
                draw_point[:] = point    #保存拖动点，覆盖上一次
                recover[-1].extend(point)#保存此次传递的点坐标到恢复记录的末次列表
        canvas.bind("<B1-Motion>", _canvas_draw) #设定拖动鼠标左键画线段
        canvas.bind("<ButtonRelease-1>", lambda event:_canvas_draw(0)) #设定松开鼠标左键清除保存的点

        #添加撤销和恢复功能rev撤销，rec恢复
        def _canvas_re(rev=0, rec=0):
            if rev and revoke: #撤销执行
                for i in revoke.pop(-1): canvas.delete(i) #pop弹出最后一个撤销列表，删除图像
            elif rec and recover and (len(revoke) != len(recover)): #恢复执行，恢复列表需要大于撤销列表
                if clear:
                    for i in recover: revoke.append([canvas.create_line(i , fill="#476042", width=1, tags = "line")])
                    clear[:] = []
                else:
                    revoke.append([canvas.create_line(recover[len(revoke)], fill="#476042", width=1, tags = "line")])

        #清空功能
        def _canvas_clear():
            canvas.delete("line") #清除 tags = "line"的图像
            revoke[:] = []
            clear.append(1)

        #添加右键菜单
        menu = tk.Menu(s.win, tearoff=0)    #不加 tearoff=0 的会出现可弹出选项
        menu.add_command(label="撤销", command = lambda:_canvas_re(rev=1))
        menu.add_command(label="恢复", command = lambda:_canvas_re(rec=1))
        menu.add_command(label="清空", command = _canvas_clear)
        canvas.bind("<Button-3>", lambda event: menu.post(event.x_root,event.y_root))#右键激活菜单

        # 创建一个Button对象，默认设置为居中对齐
        bt1 = ttk.Button(canvas,text = '撤销',command = lambda:_canvas_re(rev=1))
        #修改button在canvas上的对齐方式
        canvas.create_window((5, s.height-20), window = bt1, anchor = 'w')
        bt2 = ttk.Button(canvas,text = '恢复',command = lambda:_canvas_re(rec=1))
        canvas.create_window((s.width-90, s.height-20), window = bt2, anchor = 'w')
        bt3 = ttk.Button(canvas,text = "清空", command = _canvas_clear)
        canvas.create_window((s.width/2-43, s.height-20), window = bt3, anchor = 'w')

tkinter_example()
