from reportlab.platypus import BaseDocTemplate, Paragraph, PageTemplate, Frame, PageBreak, CondPageBreak, Table, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

from pprint import pp

class Report:
    __styles = getSampleStyleSheet()

    @staticmethod
    def __onPage(canvas, doc, pagesize=A4):
        pageNum = canvas.getPageNumber()
        canvas.drawCentredString(pagesize[0]/2, 20, str(pageNum))
    
    @staticmethod
    def __onPageLandscape(canvas, doc):
        Report.__onPage(canvas, doc, pagesize=landscape(A4))
        return None

    __padding = dict(
        leftPadding=30, 
        rightPadding=30,
        topPadding=30,
        bottomPadding=30)

    __portraitTemplate = PageTemplate(
        id = 'portrait', 
        frames = Frame(0, 0, *A4, **__padding),
        onPage = __onPage, 
        pagesize = A4)

    __landscapeTemplate = PageTemplate(
        id = 'landscape', 
        frames = Frame(0, 0, *landscape(A4), **__padding), 
        onPage=__onPageLandscape, 
        pagesize = landscape(A4))

    
    def __init__(self, path, landscape=False):
        if landscape:
            page_template = self.__landscapeTemplate
        else:
            page_template = self.__portraitTemplate
        self.page_width = page_template.frames[0]._width - self.__padding['leftPadding'] - self.__padding['rightPadding']
        self.page_heigt = page_template.frames[0]._height - self.__padding['topPadding'] - self.__padding['bottomPadding'] - 25
        self.page_heigt_left = self.page_heigt
        self.doc = BaseDocTemplate(
            '%s.pdf' % path,
            pageTemplates = [page_template]
        )
        self.story_group = []
        self.story = []

    def add_paragraph(self, text, style=__styles['Normal'], group=False):
        paragraph = Paragraph(text, style)
        if group:
            self.story_group.append(paragraph)
        else:
            self.__auto_page_break([paragraph])
            self.story.append(paragraph)

    def add_table(self, df, allign='RIGHT', symbol_link=False, group=False):
        font_size = 8
        columns = list(df.columns)
        values = df.values.tolist()
        if symbol_link and 'symbol' in columns:
            symbol_index = columns.index('symbol')
            style = self.get_style('BodyText')
            style.fontSize = font_size
            for row in values:
                symbol = row[symbol_index]
                symbol_http = '<a href="https://finance.yahoo.com/chart/%s" color="blue">%s</a>' % (symbol, symbol)
                symbol_http = Paragraph(symbol_http, style)
                row[symbol_index] = symbol_http

        table_data = [columns] + values
        table = Table(
            table_data,
            style=[
                ('FONT', (0,0), (-1,0), 'Helvetica-Bold',font_size),
                ('FONT', (0,1), (-1,-1), 'Helvetica', font_size),
                ('LINEBELOW',(0,0), (-1,0), 1, colors.black),
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), allign),
                # ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.lightgrey, colors.white]),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('LEFTPADDING', (0,0), (-1,-1), 3),  # Smaller padding
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
            ],
            hAlign = 'LEFT')
        if group:
            self.story_group.append(table)
        else:
            self.__auto_page_break([table])
            self.story.append(table)

    def add_plot_figure(self, plot_figure, group=False):
        dpi = 300
        buf = io.BytesIO()
        plot_figure.savefig(buf, format='png', dpi=dpi)
        buf.seek(0)
        x, y = plot_figure.get_size_inches()
        image =  Image(buf, x * inch, y * inch)
        if group:
            self.story_group.append(image)
        else:
            self.__auto_page_break([image])
            self.story.append(image)

    def add_space(self, inches, group=False):
        spacer = Spacer(1,inches * inch)
        if group:
            self.story_group.append(spacer)
        else:
            self.__auto_page_break([spacer])
            self.story.append(spacer)

    def add_page_break(self):
        self.page_heigt_left = self.page_heigt
        print('\nmanual page break')
        self.story.append(PageBreak())

    def add_group(self):
        if len(self.story_group) == 0: return
        self.__auto_page_break(self.story_group)
        self.story += self.story_group
        self.story_group = []
    
    def build(self):
        self.doc.build(self.story)

    def print_styles(self):
        self.__styles.list()

    def get_style(self, name):
        return self.__styles.get(name)

    def __auto_page_break(self,flowables):
        print()
        group_height = 0
        for flowable in flowables:
            size = flowable.wrap(self.page_width, self.page_heigt)
            group_height += size[1]
            print(flowable.__class__.__name__)
        self.page_heigt_left -= group_height
        print('group', group_height, self.page_heigt_left)
        if self.page_heigt_left <= 0:
            print('auto page break')
            self.add_page_break()
        
        # if isinstance(flowable, list):
        #     print('auto page break for list')
        #     for 
        # else:
        #     size = flowable.wrap(self.page_width, self.page_heigt)
        #     self.page_heigt_left -= size[1]
        #     print(flowable.__class__.__name__, size[1], self.page_heigt_left)
        #     if self.page_heigt_left <= 0:
        #         print('auto page break')
        #         self.add_page_break()
