from __future__ import annotations
from app.dto.route_stop import RouteStop
from app.services.screen.gather_route import _km
from html import escape
from urllib.parse import quote

_色 = ("#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed")


def _地図(道順ごと: dict[str, tuple[RouteStop, ...]], base: tuple[float, float] | None) -> str:
    """簡易の地図 — 座標をそのまま平面に引き伸ばして描く。**外の地図は呼ばない。**"""
    点 = [(s.lat, s.lng) for stops in 道順ごと.values() for s in stops if s.seq]
    if base:
        点.append(base)
    if not 点:
        return ""
    lat0, lat1 = min(p[0] for p in 点), max(p[0] for p in 点)
    lng0, lng1 = min(p[1] for p in 点), max(p[1] for p in 点)
    余白 = 0.004
    lat0, lat1, lng0, lng1 = lat0 - 余白, lat1 + 余白, lng0 - 余白, lng1 + 余白
    W, H = 640, 420

    def xy(lat: float, lng: float) -> tuple[float, float]:
        x = (lng - lng0) / (lng1 - lng0) * W
        y = (lat1 - lat) / (lat1 - lat0) * H
        return round(x, 1), round(y, 1)

    parts = [f"<svg viewBox='0 0 {W} {H}' style='width:100%;max-width:680px;"
             f"border:1px solid color-mix(in srgb, CanvasText 15%, transparent);"
             f"border-radius:10px;background:color-mix(in srgb, CanvasText 3%, transparent)'>"]
    for i, (担当, stops) in enumerate(sorted(道順ごと.items())):
        色 = _色[i % len(_色)]
        前 = xy(*base) if base else None
        for st in stops:
            if not st.seq:
                continue
            今 = xy(st.lat, st.lng)
            if 前:
                parts.append(f"<line x1='{前[0]}' y1='{前[1]}' x2='{今[0]}' y2='{今[1]}'"
                             f" stroke='{色}' stroke-width='2' stroke-dasharray='5 3' opacity='.75'/>")
            前 = 今
        for st in stops:
            if not st.seq:
                continue
            x, y = xy(st.lat, st.lng)
            parts.append(f"<circle cx='{x}' cy='{y}' r='11' fill='{色}'/>"
                         f"<text x='{x}' y='{y + 4}' text-anchor='middle'"
                         f" font-size='11' fill='white'>{st.seq}</text>")
    if base:
        x, y = xy(*base)
        parts.append(f"<rect x='{x - 7}' y='{y - 7}' width='14' height='14' fill='#11161d'/>"
                     f"<text x='{x}' y='{y + 22}' text-anchor='middle' font-size='10'"
                     f" fill='currentColor'>clinic</text>")
    parts.append("</svg>")
    return "".join(parts)


def _本物の地図(道順ごと: dict[str, tuple[RouteStop, ...]], base: tuple[float, float] | None, key: str) -> str:
    """Google Maps JavaScript API の地図。**鍵は窓の出自だけに効く制限つき。**"""
    import json as _json

    経路 = [
        {
            "color": _色[i % len(_色)],
            "stops": [{"lat": s.lat, "lng": s.lng, "n": s.seq, "p": s.patient}
                      for s in stops if s.seq],
        }
        for i, (_, stops) in enumerate(sorted(道順ごと.items()))
    ]
    data = _json.dumps({"base": {"lat": base[0], "lng": base[1]} if base else None, "routes": 経路})
    return (
        "<div id='gmap' style='width:100%;max-width:680px;height:440px;border-radius:10px;"
        "border:1px solid color-mix(in srgb, CanvasText 15%, transparent)'></div>"
        f"<script>const R={data};"
        "window.__troupeMap=function(){const m=new google.maps.Map("
        "document.getElementById('gmap'),{mapTypeControl:false,streetViewControl:false});"
        "const b=new google.maps.LatLngBounds();"
        "if(R.base){b.extend(R.base);new google.maps.Marker({position:R.base,map:m,"
        "label:{text:'C',color:'white'},title:'Clinic'});}"
        "for(const r of R.routes){const path=R.base?[R.base]:[];"
        "for(const s of r.stops){b.extend(s);path.push({lat:s.lat,lng:s.lng});"
        "new google.maps.Marker({position:s,map:m,label:{text:String(s.n),color:'white'},"
        "title:s.p});}"
        "new google.maps.Polyline({path,map:m,strokeColor:r.color,strokeOpacity:.8,"
        "strokeWeight:3});}"
        "m.fitBounds(b,48);};</script>"
        f"<script async src='https://maps.googleapis.com/maps/api/js?key={key}"
        "&callback=__troupeMap&loading=async'></script>"
    )


def _道順(
    day: str,
    道順ごと: dict[str, tuple[RouteStop, ...]],
    base: tuple[float, float] | None,
    maps_key: str | None = None,
    who: str | None = None,
    signed: str | None = None,
) -> str:
    from datetime import date, timedelta

    d = date.fromisoformat(day)
    前日, 翌日 = (d - timedelta(days=1)).isoformat(), (d + timedelta(days=1)).isoformat()
    who_q = f"&who={quote(who)}" if who else ""
    nav = (
        "<div class='day-bar'><span class='day-nav'>"
        f"<a href='/day?day={前日}{who_q}'>← {前日[5:]}</a> · <strong>{escape(day)}</strong>"
        f" · <a href='/day?day={翌日}{who_q}'>{翌日[5:]} →</a></span>"
        "<button class='btn btn--small push' onclick='print()'>Print day sheet</button></div>"
    )
    バナー = (
        f"<div class='banner banner--success'>✓ Signed: {escape(signed)}</div>" if signed else ""
    )
    if not 道順ごと:
        return バナー + nav + "<p class='empty'>No visits scheduled this day.</p>"

    医師たち = sorted(道順ごと)
    絞り = {who: 道順ごと[who]} if who in 道順ごと else 道順ごと
    フィルタ = (
        "<div class='filter-chips'>"
        + f"<a class='filter-chip{' is-on' if not who else ''}' href='/day?day={day}'>All</a>"
        + "".join(
            f"<a class='filter-chip{' is-on' if who == 名 else ''}'"
            f" href='/day?day={day}&who={quote(名)}'>{escape(名)}</a>"
            for 名 in 医師たち
        )
        + "</div>"
    )
    地図 = (
        _本物の地図(絞り, base, maps_key) if maps_key else _地図(絞り, base)
    )
    but = ("<p class='route-note'>Distances are straight-line estimates — not driving"
           " distance. Addresses are public landmarks standing in for homes —"
           " no real residence appears.</p>")

    帯たち = []
    節たち = []
    for i, (担当, stops) in enumerate(sorted(絞り.items())):
        予定 = [st for st in stops if st.seq]
        済み休み = [st for st in stops if not st.seq]
        署名済 = sum(1 for st in stops if st.prep == "signed")
        中止 = sum(1 for st in stops if st.status == "cancelled")
        次 = next((st for st in 予定 if st.prep != "signed" and st.status == "scheduled"), None)
        合計 = sum(float(st.leg_km) for st in 予定)
        帰路 = 0.0
        if base and 予定:
            末 = 予定[-1]
            帰路 = _km(末.lat, 末.lng, base[0], base[1])
        帯 = (
            f"<div class='progress-band'><strong>{escape(担当)}:</strong>"
            f" {署名済} of {len(stops)} signed"
            + (f" · {中止} cancelled" if 中止 else "")
            + (f" · next: {escape(次.patient)}" if 次 else " · round complete")
            + "</div>"
        )
        帯たち.append(帯)
        地点 = ([f"{base[0]},{base[1]}"] if base else []) + [
            f"{st.lat},{st.lng}" for st in 予定
        ] + ([f"{base[0]},{base[1]}"] if base and 予定 else [])
        gmap = "https://www.google.com/maps/dir/" + "/".join(地点) if 予定 else ""

        def _card(st: RouteStop) -> str:
            打消 = " stop-card--cancelled" if st.status == "cancelled" else ""
            強調 = " stop-card--next" if 次 is not None and st.visit_id == 次.visit_id else ""
            番号 = str(st.seq) if st.seq else ("✓" if st.status == "done" else "—")
            chip = (
                "<span class='chip chip--cancelled'>Cancelled</span>"
                if st.status == "cancelled"
                else f"<span class='{_CHIP[st.prep][0]}'>{_CHIP[st.prep][1]}</span>"
            )
            距離 = f"<span class='stop-card__leg'>{escape(st.leg_km)} km</span>" if st.seq else ""
            return (
                f"<li class='stop-card{打消}{強調}'>"
                f"<span class='stop-card__seq'>{番号}</span>"
                f"<span class='stop-card__main'><span class='stop-card__patient'>"
                f"<a class='patient-chip' href='/patient?code={quote(st.patient)}'>{escape(st.patient)}</a>"
                f" {escape(st.purpose)}</span>"
                f"<span class='stop-card__place sub'>{escape(st.place)}</span></span>"
                f"{chip}{距離}"
                f"<a class='link-action stop-card__open' href='/visit?id={quote(st.visit_id)}'>Open visit →</a>"
                "</li>"
            )

        節たち.append(
            f"<section class='clinician-day'><div class='clinician-day__head'>"
            f"<h3 id='{escape(担当)}' style='color:{_色[i % len(_色)]}'>{escape(担当)}</h3>"
            f"<span class='clinician-day__stats'>{len(予定)} stops · "
            f"{合計 + 帰路:.1f} km incl. return"
            + (f" · <a href='{escape(gmap)}'>open in Google Maps</a>" if gmap else "")
            + "</span></div>"
            + "<ol class='stop-list'>"
            + "".join(_card(st) for st in stops)
            + "</ol>"
            + (f"<div class='stop-return'>⌂ Return to clinic · {帰路:.1f} km</div>" if base and 予定 else "")
            + "</section>"
        )
    # 2面 — 左：日送り・進み具合・地図・注記／右：絞り込みと回る先。バナーは全幅で最上段
    return (
        バナー
        + "<div class='day-grid'>"
        + "<div class='day-map'>"
        + nav
        + "".join(帯たち)
        + f"<div class='map-slot'>{地図}</div>"
        + but
        + "</div>"
        + "<div class='day-stops'>"
        + フィルタ
        + "".join(節たち)
        + "</div>"
        + "</div>"
    )



_CHIP = {"signed": ("chip chip--signed", "Signed ✓"),
         "draft": ("chip chip--draft-ready", "Draft ready ✓"),
         "none": ("chip chip--no-draft", "No draft yet")}


