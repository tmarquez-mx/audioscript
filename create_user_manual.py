from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib import colors
import os, textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output", "pdf", "Manual_de_usuario_AudioScript_Contextual.pdf")
W, H = A4

NAVY = HexColor("#16273F")
BLUE = HexColor("#294E73")
INK = HexColor("#2B3443")
MUTED = HexColor("#667383")
RUST = HexColor("#C36A3C")
ORANGE = HexColor("#D98A5A")
CREAM = HexColor("#FBFAF4")
SAND = HexColor("#F3F0E4")
SAGE = HexColor("#DBE8DE")
GREEN = HexColor("#3C7657")
PALEBLUE = HexColor("#E8EFF6")
WHITE = colors.white
RED = HexColor("#A64B42")

REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SERIF_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
pdfmetrics.registerFont(TTFont("AS", REG))
pdfmetrics.registerFont(TTFont("AS-B", BOLD))
pdfmetrics.registerFont(TTFont("AS-S", SERIF))
pdfmetrics.registerFont(TTFont("AS-SB", SERIF_B))


def rr(c, x, y, w, h, r=10, fill=WHITE, stroke=None, sw=1):
    c.setLineWidth(sw)
    if fill: c.setFillColor(fill)
    if stroke: c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, r, fill=1 if fill else 0, stroke=1 if stroke else 0)


def txt(c, text, x, y, size=10, font="AS", color=INK, maxw=None, leading=None, align="left"):
    c.setFont(font, size); c.setFillColor(color)
    if maxw is None:
        c.drawString(x, y, text); return y-size
    leading = leading or size*1.3
    words = text.split(); lines=[]; line=""
    for word in words:
        test = (line+" "+word).strip()
        if stringWidth(test, font, size) <= maxw: line=test
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    for ln in lines:
        if align == "center": c.drawCentredString(x+maxw/2, y, ln)
        elif align == "right": c.drawRightString(x+maxw, y, ln)
        else: c.drawString(x, y, ln)
        y -= leading
    return y


def label(c, s, x, y, fill=RUST, color=WHITE, w=None):
    w = w or stringWidth(s.upper(), "AS-B", 7.3)+16
    rr(c, x, y-2, w, 18, 9, fill)
    c.setFillColor(color); c.setFont("AS-B", 7.3); c.drawCentredString(x+w/2, y+4, s.upper())
    return w


def icon(c, kind, x, y, r=14, fill=NAVY):
    c.setFillColor(fill); c.circle(x, y, r, fill=1, stroke=0)
    c.setStrokeColor(WHITE); c.setFillColor(WHITE); c.setLineWidth(1.8)
    if kind == "check":
        c.line(x-r*.45,y, x-r*.1,y-r*.35); c.line(x-r*.1,y-r*.35,x+r*.5,y+r*.35)
    elif kind == "lock":
        c.roundRect(x-r*.45,y-r*.45,r*.9,r*.75,2,fill=0,stroke=1); c.arc(x-r*.3,y+r*.05,x+r*.3,y+r*.65,0,180)
    elif kind == "folder":
        c.rect(x-r*.55,y-r*.35,r*1.1,r*.7,fill=0,stroke=1); c.line(x-r*.45,y+r*.35,x-r*.15,y+r*.6); c.line(x-r*.15,y+r*.6,x+r*.15,y+r*.6)
    elif kind == "play":
        p=c.beginPath(); p.moveTo(x-r*.25,y-r*.42);p.lineTo(x+r*.48,y);p.lineTo(x-r*.25,y+r*.42);p.close();c.drawPath(p,fill=1,stroke=0)
    elif kind == "download":
        c.line(x,y+r*.45,x,y-r*.15); c.line(x,y-r*.15,x-r*.3,y+r*.1);c.line(x,y-r*.15,x+r*.3,y+r*.1);c.line(x-r*.45,y-r*.5,x+r*.45,y-r*.5)
    elif kind == "memo":
        c.rect(x-r*.45,y-r*.5,r*.9,r,fill=0,stroke=1); c.line(x-r*.28,y+r*.2,x+r*.28,y+r*.2);c.line(x-r*.28,y,x+r*.2,y)
    else:
        c.setFont("AS-B", r); c.drawCentredString(x,y-r*.34,kind[:1].upper())


def page_base(c, n, section="MANUAL DE USUARIO", dark=False):
    if dark:
        c.setFillColor(NAVY); c.rect(0,0,W,H,fill=1,stroke=0)
        return
    c.setFillColor(CREAM); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(SAGE); c.circle(-20,H+5,130,fill=1,stroke=0)
    c.setFillColor(RUST); c.rect(0,0,7,H,fill=1,stroke=0)
    c.setStrokeColor(HexColor("#D7D5CC")); c.line(42,31,W-42,31)
    c.setFont("AS-B",7); c.setFillColor(MUTED); c.drawString(42,19,section)
    c.drawRightString(W-42,19,f"AUDIOSCRIPT CONTEXTUAL  |  {n:02d}")


def heading(c, kicker, title, sub=None, y=770):
    label(c,kicker,42,y,fill=RUST)
    y-=40
    y=txt(c,title,42,y,25,"AS-SB",NAVY,W-84,29)
    if sub: y=txt(c,sub,42,y-7,10.5,"AS",MUTED,W-84,14)
    return y-16


def step(c, n, title, body, x, y, w, h=72, accent=RUST):
    rr(c,x,y-h,w,h,12,WHITE,HexColor("#DEDCD3"))
    c.setFillColor(accent); c.circle(x+25,y-24,14,fill=1,stroke=0)
    c.setFillColor(WHITE);c.setFont("AS-B",10);c.drawCentredString(x+25,y-27,str(n))
    txt(c,title,x+48,y-18,10,"AS-B",NAVY,w-62,12)
    txt(c,body,x+48,y-37,8.4,"AS",INK,w-62,11)


def callout(c, title, body, x, y, w, h, color=SAGE, symbol="i"):
    rr(c,x,y-h,w,h,12,color,None)
    icon(c,symbol,x+24,y-24,11,NAVY)
    txt(c,title,x+43,y-19,9.5,"AS-B",NAVY,w-55,12)
    txt(c,body,x+43,y-39,8.4,"AS",INK,w-55,11)


def mini_ui(c, x, y, w, h, active=3):
    rr(c,x,y-h,w,h,12,WHITE,HexColor("#CDD3D8"))
    c.setFillColor(NAVY); c.roundRect(x,y-32,w,32,12,fill=1,stroke=0); c.rect(x,y-32,w,17,fill=1,stroke=0)
    c.setFillColor(RUST);c.circle(x+20,y-16,7,fill=1,stroke=0)
    txt(c,"AudioScript Contextual",x+34,y-20,8,"AS-SB",WHITE)
    side=116
    c.setFillColor(HexColor("#F5F7F9"));c.rect(x,y-h,side,h-32,fill=1,stroke=0)
    items=["1  Proyecto","2  Material","3  Preparación","4  Transcribir"]
    for i,s in enumerate(items):
        yy=y-54-i*31
        if i+1==active: rr(c,x+8,yy-17,side-16,24,7,PALEBLUE,None)
        c.setFillColor(GREEN if i+1<active else RUST if i+1==active else MUTED);c.circle(x+21,yy-5,7,fill=1,stroke=0)
        txt(c,s,x+34,yy-8,6.8,"AS-B" if i+1==active else "AS",INK)
    mx=x+side+16
    txt(c,"Mesa del proyecto",mx,y-55,12,"AS-SB",NAVY)
    rr(c,mx,y-68,w-side-32,44,8,SAND,None)
    txt(c,"Proyecto  |  Material activo  |  Fecha  |  Segmentos",mx+12,y-87,6.7,"AS-B",MUTED)
    rr(c,mx,y-124,w-side-32,h-140,8,CREAM,HexColor("#DDDAD0"))
    icon(c,"play",mx+(w-side-32)/2,y-186,18,BLUE)
    txt(c,"Reproductor de audio / video",mx+20,y-218,7.3,"AS-B",MUTED,w-side-72,10,align="center")
    txt(c,"Documento de transcripción",mx+14,y-145,8.5,"AS-B",NAVY)
    for i in range(7):
        c.setStrokeColor(HexColor("#C8CDD1"));c.line(mx+14,y-164-i*13,x+w-29-(i%3)*22,y-164-i*13)
    rr(c,x+w-126,y-h+16,102,55,8,PALEBLUE,None)
    txt(c,"Mesa de análisis",x+w-116,y-h+51,7.5,"AS-B",NAVY)
    txt(c,"Memos  ·  Códigos",x+w-116,y-h+34,6.7,"AS",INK)


def cover(c):
    page_base(c,1,dark=True)
    c.setFillColor(BLUE);c.circle(W+15,H-40,225,fill=1,stroke=0)
    c.setFillColor(RUST);c.circle(W-58,H-100,82,fill=1,stroke=0)
    c.setFillColor(Color(1,1,1,.06));
    for i in range(11): c.circle(54+i*49,175+(i%3)*12,30+(i%4)*8,fill=0,stroke=1)
    c.setStrokeColor(ORANGE); c.setLineWidth(2)
    for i,h in enumerate([10,17,27,14,22]): c.line(46+i*9,H-127,46+i*9,H-127+h)
    c.line(45,H-133,63,H-133)
    wave=c.beginPath(); wave.moveTo(63,H-133); wave.curveTo(68,H-124,73,H-124,77,H-133); wave.curveTo(82,H-142,87,H-142,92,H-133); c.drawPath(wave,fill=0,stroke=1)
    txt(c,"AudioScript",115,H-117,18,"AS-SB",RUST)
    txt(c,"Contextual",220,H-117,18,"AS-SB",WHITE)
    txt(c,"TRANSCRIPCIÓN INMERSIVA · DATOS LOCALES",115,H-139,7.2,"AS-B",HexColor("#DCE5EF"))
    label(c,"BETA 0.9 · MAC",42,590,fill=RUST)
    txt(c,"Manual de usuario",42,530,38,"AS-SB",WHITE,W-84,42)
    txt(c,"Instala, transcribe y analiza con confianza.",42,466,18,"AS-S",HexColor("#DCE5EF"),W-100,23)
    txt(c,"Una guía visual y didáctica para convertir audio y video en documentos de trabajo, memos y códigos, manteniendo tus datos en tu Mac.",42,406,11,"AS",WHITE,420,16)
    rr(c,42,265,250,78,14,Color(1,1,1,.09),Color(1,1,1,.18))
    icon(c,"lock",68,304,15,RUST)
    txt(c,"Privacidad local",94,313,10,"AS-B",WHITE)
    txt(c,"Después de la descarga inicial del modelo, el procesamiento ocurre en tu equipo.",94,292,8.3,"AS",HexColor("#DCE5EF"),180,11)
    txt(c,"EDICIÓN JUNIO 2026",42,60,8,"AS-B",ORANGE)


def p2(c):
    page_base(c,2); y=heading(c,"EMPIEZA AQUÍ","Tu ruta en 6 movimientos","Este mapa resume el flujo completo. Cada paso se desarrolla en las páginas siguientes.")
    coords=[(42,610),(304,610),(42,490),(304,490),(42,370),(304,370)]
    data=[("Instala","Copia la app a Aplicaciones y autoriza la apertura."),("Prepara","Descarga Medium o Large una sola vez."),("Crea","Abre un proyecto y carga un audio o video."),("Configura","Elige modo, idioma, segmentos y formato."),("Trabaja","Transcribe, corrige, agrega memos y códigos."),("Exporta","Descarga Word, Excel o QDC para continuar.")]
    for i,((x,yy),(t,b)) in enumerate(zip(coords,data),1): step(c,i,t,b,x,yy,249,88, RUST if i in [1,2,5] else BLUE)
    callout(c,"Regla de oro","Primero confirma que estás en el proyecto correcto. Después selecciona el material activo y revisa la preparación antes de transcribir.",42,236,W-84,70,SAGE,"check")
    txt(c,"LEYENDA VISUAL",42,139,8,"AS-B",MUTED)
    label(c,"RECOMENDADO",42,104,fill=GREEN); label(c,"ATENCIÓN",163,104,fill=RUST); label(c,"DATO LOCAL",246,104,fill=BLUE)


def p3(c):
    page_base(c,3); heading(c,"ANTES DE INSTALAR","Requisitos y preparación","Cinco comprobaciones evitan casi todos los tropiezos del primer inicio.")
    items=[("Mac compatible","Apple Silicon: M1, M2, M3, M4 o M5."),("Sistema","macOS 13 Ventura o posterior."),("Conexión inicial","Internet sólo para descargar el modelo Whisper."),("Espacio libre","Reserva varios GB; Large ocupa y consume más que Medium."),("Permisos","Necesitarás autorización de administrador o Touch ID.")]
    for i,(t,b) in enumerate(items):
        x=42+(i%2)*262; yy=620-(i//2)*108; step(c,i+1,t,b,x,yy,249,82,BLUE)
    callout(c,"¿Qué viene incluido?","Python, Streamlit, Whisper, Torch, ffmpeg y los componentes necesarios. No necesitas Homebrew, Terminal ni instalar Python.",42,280,W-84,75,PALEBLUE,"check")
    callout(c,"Compatibilidad de esta beta","La versión descrita en este manual es exclusivamente para Mac con Apple Silicon. No instales este DMG en Mac Intel o Windows.",42,184,W-84,75,HexColor("#F6E6DF"),"!")


def p4(c):
    page_base(c,4); heading(c,"INSTALACIÓN","Instala la app con seguridad","macOS puede bloquear la primera apertura porque esta beta aún no está notarizada por Apple.")
    data=[("Abre el DMG","Haz doble clic en AudioScript_Contextual_Beta_Mac.dmg."),("Arrastra la app","Mueve AudioScript Contextual.app a Aplicaciones."),("Haz clic derecho","En Aplicaciones, clic derecho sobre la app y elige Abrir."),("No la elimines","Si Apple no pudo verificarla, pulsa Listo. No elijas Mover al basurero."),("Autoriza","Ajustes del Sistema > Privacidad y seguridad > Abrir de todos modos."),("Confirma","Usa Touch ID o contraseña y vuelve a elegir Abrir.")]
    for i,(t,b) in enumerate(data):
        x=42+(i%2)*262; yy=630-(i//2)*112; step(c,i+1,t,b,x,yy,249,88,RUST if i>=3 else BLUE)
    # settings mockup
    rr(c,42,238,W-84,111,14,WHITE,HexColor("#D5D8DC"))
    c.setFillColor(HexColor("#E7E9EC"));c.rect(42,321,W-84,28,fill=1,stroke=0)
    c.setFillColor(RED);c.circle(57,335,4,fill=1,stroke=0);c.setFillColor(HexColor("#E7B044"));c.circle(70,335,4,fill=1,stroke=0);c.setFillColor(GREEN);c.circle(83,335,4,fill=1,stroke=0)
    txt(c,"Privacidad y seguridad",104,331,8,"AS-B",NAVY)
    icon(c,"lock",75,281,16,NAVY)
    txt(c,"Se bloqueó el uso de AudioScript Contextual",105,295,8.5,"AS-B",INK)
    txt(c,"porque no proviene de un desarrollador identificado.",105,278,7.5,"AS",MUTED)
    rr(c,390,263,124,30,8,NAVY,None);txt(c,"Abrir de todos modos",400,274,7.4,"AS-B",WHITE)
    callout(c,"Si el botón no aparece","Intenta abrir la app una vez y regresa inmediatamente a Privacidad y seguridad. El botón sólo aparece después del primer bloqueo.",42,208,W-84,72,HexColor("#F6E6DF"),"!")


def p5(c):
    page_base(c,5); heading(c,"PRIMER INICIO","Descarga el motor de transcripción","El modelo de Whisper es la única descarga necesaria para usar AudioScript.")
    rr(c,42,560,245,150,16,WHITE,HexColor("#D8DAD7")); label(c,"RECOMENDADO",59,681,fill=GREEN)
    txt(c,"MEDIUM",59,646,23,"AS-SB",NAVY);txt(c,"Buen equilibrio entre precisión, velocidad y memoria para entrevistas y trabajo cualitativo.",59,612,9,"AS",INK,208,13)
    rr(c,59,576,109,28,7,GREEN,None);txt(c,"Elegir Medium",73,586,8,"AS-B",WHITE)
    rr(c,308,560,245,150,16,WHITE,HexColor("#D8DAD7")); label(c,"MÁS EXIGENTE",325,681,fill=RUST)
    txt(c,"LARGE",325,646,23,"AS-SB",NAVY);txt(c,"Puede ayudar con audio difícil, pero requiere más espacio, memoria y tiempo de proceso.",325,612,9,"AS",INK,208,13)
    rr(c,325,576,99,28,7,NAVY,None);txt(c,"Elegir Large",338,586,8,"AS-B",WHITE)
    y=518
    for i,(t,b) in enumerate([("Mantén internet","No cierres la app ni desconectes la Mac durante la descarga."),("Espera la confirmación","La primera descarga puede tardar. Después, el modelo queda guardado localmente."),("Trabaja sin conexión","Cuando termina, puedes desconectar internet y seguir transcribiendo.")],1):
        step(c,i,t,b,42,y-(i-1)*86,W-84,68,BLUE)
    callout(c,"Ubicación del modelo","~/Library/Application Support/AudioScript Contextual/whisper_models",42,234,W-84,62,PALEBLUE,"folder")
    callout(c,"¿Ves localhost en el navegador?","Es normal: la interfaz pertenece a la aplicación que se ejecuta en tu propia Mac. No es un servidor remoto de AudioScript.",42,151,W-84,65,SAGE,"lock")


def p6(c):
    page_base(c,6); heading(c,"ORIENTACIÓN","La interfaz de un vistazo","La barra lateral prepara el trabajo; la mesa central permite escuchar, editar y analizar.")
    mini_ui(c,42,625,W-84,285,active=3)
    notes=[("A","Ruta guiada","Proyecto > Material > Preparación > Transcribir."),("B","Mesa central","Reproduce, transcribe y corrige el contenido."),("C","Mesa de análisis","Crea memos y códigos mientras lees."),("D","Exportaciones","Descarga el avance incluso antes de terminar.")]
    for i,(letter,t,b) in enumerate(notes):
        x=42+(i%2)*262; yy=308-(i//2)*94
        icon(c,letter,x+16,yy-14,14,RUST if i in [0,2] else BLUE)
        txt(c,t,x+39,yy-10,9.5,"AS-B",NAVY)
        txt(c,b,x+39,yy-30,8.3,"AS",INK,210,11)
    callout(c,"Consejo","Si no sabes qué sigue, usa el botón principal de la barra lateral: cambia de forma contextual según el estado del proyecto.",42,128,W-84,64,SAGE,"check")


def p7(c):
    page_base(c,7); heading(c,"PROYECTOS Y MATERIALES","Organiza antes de transcribir","Un proyecto puede reunir varios audios o videos, junto con sus segmentos, memos, códigos y exportaciones.")
    # hierarchy visual
    rr(c,42,566,511,104,16,NAVY,None);icon(c,"folder",76,617,19,RUST);txt(c,"PROYECTO: Entrevistas de campo",108,627,13,"AS-SB",WHITE);txt(c,"Contexto, fechas, ajustes y avance",108,604,8.5,"AS",HexColor("#DCE5EF"))
    for i,name in enumerate(["Entrevista 01.m4a","Grupo focal.mp4","Nota de voz.wav"]):
        x=42+i*174;rr(c,x,535,163,66,10,WHITE,HexColor("#D8DAD7"));icon(c,"play",x+24,568,12,BLUE);txt(c,name,x+43,573,7.7,"AS-B",NAVY,110,10);txt(c,"Material",x+43,550,7,"AS",MUTED)
    data=[("Crea o abre","Usa + Crear o abrir proyecto. Pon un título reconocible."),("Carga material","Seleccionar y activar material admite audio o video."),("Divide si hace falta","Quick Split crea partes temporales y puede buscar silencios."),("Verifica lo activo","La Mesa del proyecto muestra el material actual antes de iniciar.")]
    for i,(t,b) in enumerate(data):
        x=42+(i%2)*262;yy=430-(i//2)*100;step(c,i+1,t,b,x,yy,249,76,BLUE)
    callout(c,"Archivos grandes","Si el archivo supera el límite recomendado, ajusta la división. Buscar silencios reduce cortes a mitad de palabra, aunque el tiempo final de cada parte puede variar.",42,224,W-84,72,PALEBLUE,"!")
    callout(c,"Tus originales no se borran","AudioScript vincula o copia material de trabajo, pero no elimina el archivo original que seleccionaste.",42,132,W-84,60,SAGE,"lock")


def p8(c):
    page_base(c,8); heading(c,"PREPARACIÓN","Configura según tu material","Confirma estos ajustes antes de transcribir; modificarlos después puede cambiar el resultado.")
    rows=[("Modo","Segmentado","Recomendado para entrevistas y análisis cualitativo."),("Idioma","Español / Automático","Elige Español si todo el audio está en ese idioma."),("Segmentos","1 a 30 min","Partes cortas facilitan revisar y retomar el avance."),("Modelo","Medium","Equilibrio recomendado; usa Large para audio difícil."),("Formato","Limpia / Verbatim","Limpia quita muletillas; Verbatim conserva pausas y risas."),("Términos","Nombres y tecnicismos","Añade personas, lugares, siglas y vocabulario especializado.")]
    yy=632
    for i,(a,b,d) in enumerate(rows):
        fill=WHITE if i%2==0 else HexColor("#F5F3EB");rr(c,42,yy-62,W-84,57,8,fill,None)
        label(c,a,55,yy-28,fill=BLUE,w=74);txt(c,b,143,yy-22,9,"AS-B",NAVY,130,11);txt(c,d,285,yy-22,8.2,"AS",INK,250,11);yy-=64
    callout(c,"No olvides confirmar","Pulsa Confirmar preparación. La ruta lateral marcará el paso como completado y habilitará la transición natural a Transcribir.",42,218,W-84,68,SAGE,"check")
    callout(c,"Completo o segmentado","Usa Completo sólo para audios muy cortos. Segmentado protege mejor el avance, simplifica la revisión y permite continuar por partes.",42,130,W-84,68,PALEBLUE,"i")


def p9(c):
    page_base(c,9); heading(c,"TRANSCRIPCIÓN Y REVISIÓN","Del audio al texto confiable","La transcripción automática es un borrador: escuchar y corregir sigue siendo parte del método.")
    mini_ui(c,42,626,W-84,215,active=4)
    flow=[("1","Transcribir","Inicia el segmento activo."),("2","Escuchar","Contrasta el texto con el reproductor."),("3","Corregir","Edita nombres, puntuación y pasajes dudosos."),("4","Confirmar","Guarda y avanza al siguiente segmento.")]
    for i,(n,t,b) in enumerate(flow):
        x=42+i*129; icon(c,n,x+20,366,15,RUST if i in [0,3] else BLUE);txt(c,t,x+43,371,8.6,"AS-B",NAVY,80,10);txt(c,b,x+43,349,7.4,"AS",INK,78,10)
    callout(c,"Revisión eficiente","Añade nombres y términos técnicos antes de transcribir. Usa el reemplazo para corregir una forma repetida y el Modo lectura cuando necesites concentración visual.",42,302,W-84,72,SAGE,"check")
    step(c,1,"Trabajo por segmentos","La navegación indica Segmento 1 de N y conserva el avance del material.",42,210,249,75,BLUE)
    step(c,2,"Documento consolidado","Al terminar, revisa el texto completo antes de exportar.",304,210,249,75,BLUE)
    callout(c,"Evita perder el contexto","No cambies de proyecto o material sin confirmar cuál está activo. Revisa la tarjeta Mesa del proyecto antes de continuar una sesión.",42,114,W-84,60,HexColor("#F6E6DF"),"!")


def p10(c):
    page_base(c,10); heading(c,"ANÁLISIS Y SALIDA","Memos, códigos y exportación","AudioScript acompaña la lectura analítica sin obligarte a salir de la transcripción.")
    cards=[("memo","MEMOS","Registra observaciones, hipótesis, decisiones y preguntas ligadas al segmento."),("C","CÓDIGOS","Selecciona una frase y crea códigos preliminares con notas de interpretación."),("download","EXPORTAR","Genera entregables aun cuando queden segmentos pendientes.")]
    for i,(ic,t,b) in enumerate(cards):
        x=42+i*174;rr(c,x,540,163,140,14,WHITE,HexColor("#D8DAD7"));icon(c,ic,x+29,649,16,RUST if i==1 else BLUE);txt(c,t,x+53,655,9,"AS-B",NAVY);txt(c,b,x+17,617,8.2,"AS",INK,129,12)
    txt(c,"FORMATOS DE SALIDA",42,506,9,"AS-B",MUTED)
    formats=[("DOCX","Transcripción con contexto, memos y códigos."),("XLSX MEMOS","Tabla para ordenar y revisar notas analíticas."),("XLSX CÓDIGOS","Inventario de códigos y fragmentos asociados."),("QDC","Codebook compatible con flujos cualitativos.")]
    for i,(f,b) in enumerate(formats):
        yy=472-i*58;rr(c,42,yy-44,W-84,48,8,WHITE,None);label(c,f,55,yy-28,fill=BLUE,w=82);txt(c,b,151,yy-22,8.5,"AS",INK,380,11)
    callout(c,"Exporta durante el proceso","No necesitas terminar todos los segmentos para sacar un respaldo de trabajo. La exportación parcial ayuda a revisar, compartir o archivar avances.",42,211,W-84,68,SAGE,"download")
    callout(c,"Control metodológico","Usa los códigos como pre-codificación y documenta decisiones en memos. La interpretación sigue siendo tuya; el sistema organiza el rastro de análisis.",42,124,W-84,65,PALEBLUE,"memo")


def p11(c):
    page_base(c,11); heading(c,"PRIVACIDAD Y ARCHIVOS","Tus datos permanecen en tu Mac","Después de instalar el modelo, audios, transcripciones, memos y códigos no se envían a un servidor de AudioScript.")
    c.setFillColor(NAVY);c.circle(W/2,557,88,fill=1,stroke=0);icon(c,"lock",W/2,574,31,RUST);txt(c,"PROCESAMIENTO LOCAL",W/2-80,526,10,"AS-B",WHITE,160,12,align="center")
    for ang,(t,b) in zip([150,30,235,305],[('Audio / video','Material de investigación'),('Transcripción','Texto y correcciones'),('Memos','Notas interpretativas'),('Códigos','Pre-codificación')]):
        import math
        x=W/2+math.cos(math.radians(ang))*180;y=557+math.sin(math.radians(ang))*105
        rr(c,x-70,y-28,140,56,10,WHITE,HexColor("#D8DAD7"));txt(c,t,x-60,y+7,8.3,"AS-B",NAVY,120,10,align="center");txt(c,b,x-60,y-11,7,"AS",MUTED,120,9,align="center")
    txt(c,"UBICACIONES LOCALES",42,350,9,"AS-B",MUTED)
    callout(c,"Proyectos","~/Library/Application Support/AudioScript Contextual/Projects",42,322,W-84,58,PALEBLUE,"folder")
    callout(c,"Modelos Whisper","~/Library/Application Support/AudioScript Contextual/whisper_models",42,247,W-84,58,SAGE,"folder")
    callout(c,"Diagnóstico","~/Library/Logs/AudioScript Contextual/launcher.log",42,172,W-84,58,HexColor("#F4EEE4"),"i")
    txt(c,"Buenas prácticas",42,94,9,"AS-B",NAVY)
    txt(c,"Usa nombres de proyecto no sensibles · protege tu sesión de macOS · conserva copias de las exportaciones · no compartas audios para reportar fallos.",42,75,8.1,"AS",INK,W-84,11)


def p12(c):
    page_base(c,12); heading(c,"AYUDA RÁPIDA","Cuando algo no sale como esperabas","Empieza por la causa más común y avanza en orden.")
    issues=[("La app no abre","Comprueba Apple Silicon y macOS 13+. Usa clic derecho > Abrir y luego Privacidad y seguridad > Abrir de todos modos."),("No aparece Abrir de todos modos","Intenta abrir la app otra vez y vuelve inmediatamente a Privacidad y seguridad."),("La descarga parece detenida","Mantén internet, evita cerrar la app y deja espacio libre. Medium suele ser la opción más práctica."),("El audio es muy grande","Usa Quick Split y activa la búsqueda de silencios para obtener partes manejables."),("La transcripción falla en nombres","Añade nombres y términos técnicos, confirma idioma y vuelve a intentar el segmento."),("Necesitas reportar un error","Indica acción realizada, mensaje visible, versión de macOS y modelo de Mac. No envíes el audio ni la transcripción.")]
    yy=650
    for i,(q,a) in enumerate(issues):
        x=42+(i%2)*262;y=yy-(i//2)*135
        rr(c,x,y-112,249,105,12,WHITE,HexColor("#DEDCD3"));label(c,f"0{i+1}",x+14,y-32,fill=RUST,w=34);txt(c,q,x+58,y-25,9,"AS-B",NAVY,174,11);txt(c,a,x+16,y-56,7.9,"AS",INK,217,11)
    callout(c,"Cierre correcto","Para detener el servidor local, usa Salir sobre el icono de AudioScript o cierra la aplicación. Cerrar sólo la pestaña del navegador puede dejar la app activa.",42,219,W-84,69,PALEBLUE,"!")
    rr(c,42,67,W-84,102,14,NAVY,None)
    txt(c,"Tu trabajo, bajo tu control.",62,134,16,"AS-SB",WHITE)
    txt(c,"AudioScript Contextual convierte material audiovisual en una mesa de transcripción y análisis local, trazable y exportable.",62,108,8.7,"AS",HexColor("#DCE5EF"),390,12)
    icon(c,"check",503,118,23,RUST)


def build():
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    c=canvas.Canvas(OUT,pagesize=A4,pageCompression=1)
    c.setTitle("Manual de usuario - AudioScript Contextual")
    c.setAuthor("AudioScript Contextual")
    funcs=[cover,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12]
    for fn in funcs:
        fn(c);c.showPage()
    c.save();print(OUT)

if __name__ == '__main__': build()
