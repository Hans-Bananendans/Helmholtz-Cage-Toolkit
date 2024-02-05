from helmholtz_cage_toolkit import *

class EnvelopePlot(pg.GraphicsLayoutWidget):
    def __init__(self, datapool):
        super().__init__()

        self.datapool = datapool
        self.datapool.cyclics_plot = self

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        self.plot_obj.showGrid(x=True, y=True)
        self.plot_obj.showAxis('bottom', True)
        self.plot_obj.showAxis('left', True)
        self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj.getAxis("left").setLabel(text="B", units="T")
        self.plot_obj.getAxis("left").setScale(scale=1E-9)

        self.vline = pg.InfiniteLine(angle=90, movable=False,
                                     pen=pg.mkPen("c", width=2),)
        self.vline.setZValue(10)
        self.plot_obj.addItem(self.vline, ignoreBounds=True)

        self.generate_envelope_plot()

    def generate_envelope_plot(self, show_actual=True, show_points=False):

        t = self.datapool.schedule[2]
        B = array([self.datapool.schedule[3],
                   self.datapool.schedule[4],
                   self.datapool.schedule[5]])

        colours = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]

        # Generate staggered dataset by copying using repeat and then shifting
        push = [0, -1]
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        B_stag = array((repeat(B[0, push[0]:push[1]], 2)[:-1],
                        repeat(B[1, push[0]:push[1]], 2)[:-1],
                        repeat(B[2, push[0]:push[1]], 2)[:-1])
                       )

        for i in range(3):
            if show_actual:
                # Staggered line
                self.plot_obj.plot(t_stag, B_stag[i], pen=colours[i])

            else:
                self.plot_obj.plot(t, B[i], pen=colours[i])

            if show_points:
                self.plot_obj.plot(t, B[i],
                                   pen=(0, 0, 0, 0),
                                   symbolBrush=(0, 0, 0, 0),
                                   symbolPen=colours[i],
                                   symbol="o",
                                   symbolSize=6)