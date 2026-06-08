#!/usr/bin/env python3
"""Generate ActiveState-styled index.html and scan_report.html from existing data."""
import json, datetime, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_JSON   = os.path.join(ROOT, "..", "indexUI", "data.json")
AUDIT_JSON  = os.path.join(ROOT, "..", "indexUI", "results", "audit.json")

# ── shared assets ────────────────────────────────────────────────────────────

LOGO_SVG = '''<svg width="135" height="24" viewBox="0 0 135.279 23.9282" fill="none" xmlns="http://www.w3.org/2000/svg"><g><path d="M7.7681 10.0153V11.8614V15.1514C7.7681 16.0009 8.22211 16.7932 8.95469 17.2188L10.1998 17.9415L11.7896 17.0192L9.75036 15.8354C9.50874 15.6945 9.35791 15.433 9.35791 15.1514V11.8165V9.09299V2.38776C9.35791 2.1773 9.43948 1.97923 9.58723 1.82912C9.73497 1.68056 9.93197 1.59855 10.1428 1.59855H16.6144C17.0469 1.59855 17.3993 1.95292 17.3993 2.38776V7.2453L18.9891 8.16759V2.38776C18.9891 1.07086 17.9241 0 16.6144 0H10.1428C9.50874 0 8.91159 0.249144 8.46374 0.69946C8.01588 1.14978 7.7681 1.7502 7.7681 2.38776V10.0153Z" fill="#1257b2"/><path d="M14.9658 18.8638L17.8022 17.2173C18.5348 16.7917 18.9888 15.9994 18.9888 15.1498V13.7091L17.399 12.7868V15.1514C17.399 15.433 17.2482 15.6945 17.0066 15.8354L14.2963 17.4092L10.7643 19.4611L6.001 22.2249C5.8194 22.3301 5.60855 22.358 5.4054 22.3038C5.20225 22.2497 5.03295 22.1181 4.9283 21.9355L1.69173 16.2996C1.47473 15.9236 1.60401 15.4392 1.97953 15.221L6.17491 12.7853V10.9391L1.18693 13.8345C0.0526676 14.4922 -0.336706 15.9561 0.31738 17.0966L3.55395 22.7325C3.87099 23.2849 4.38349 23.6795 4.99602 23.8451C5.20071 23.9008 5.40848 23.9271 5.61471 23.9271C6.02563 23.9271 6.43193 23.8188 6.79822 23.6068L13.3776 19.7876L14.9674 18.8653L14.9658 18.8638Z" fill="#1257b2"/><path d="M25.5605 13.8345L18.9889 10.0168V10.0137L17.3991 9.09145V9.09454L14.5673 7.44802C14.201 7.23447 13.7901 7.12924 13.3791 7.12924C12.9682 7.12924 12.5573 7.23602 12.1925 7.44802L10.949 8.1707V10.0168L12.9882 8.83302C13.2298 8.6922 13.5315 8.6922 13.7731 8.83302L17.4006 10.9407L20.5956 12.7961L24.7648 15.221C25.1388 15.4392 25.2681 15.922 25.0511 16.2981L21.8145 21.934C21.7099 22.1166 21.5406 22.2466 21.3374 22.3023C21.1343 22.3564 20.9234 22.3286 20.7418 22.2234L16.5541 19.7892L14.9643 20.7115L19.9462 23.6068C20.4956 23.9256 21.1358 24.0107 21.7484 23.8467C22.3609 23.6811 22.8734 23.2865 23.1904 22.734L26.427 17.0981C27.0811 15.9592 26.6917 14.4952 25.559 13.8376" fill="#1257b2"/><path d="M34.3715 10.3682C34.8086 9.54646 35.4104 8.91044 36.1768 8.45703C36.9417 8.00362 37.7943 7.77769 38.7347 7.77769C39.675 7.77769 40.4645 7.97886 41.1478 8.37966C41.8296 8.78045 42.3375 9.28493 42.673 9.89309V7.95255H44.4491V18.5884H42.673V16.6091C42.3252 17.2297 41.8081 17.745 41.1186 18.152C40.4307 18.559 39.6288 18.7632 38.7162 18.7632C37.8035 18.7632 36.9278 18.5296 36.1691 18.0638C35.4104 17.598 34.8117 16.945 34.3746 16.1031C33.9375 15.2628 33.719 14.305 33.719 13.231C33.719 12.1571 33.9375 11.1899 34.3746 10.3682M42.1882 11.1543C41.8666 10.5601 41.4326 10.1035 40.8847 9.78632C40.3383 9.46908 39.7366 9.31124 39.0794 9.31124C38.4222 9.31124 37.8251 9.46599 37.2849 9.77703C36.7447 10.0881 36.3138 10.5415 35.9921 11.1357C35.6705 11.7315 35.5089 12.4294 35.5089 13.231C35.5089 14.0326 35.6689 14.7553 35.9921 15.3557C36.3138 15.9577 36.7447 16.4173 37.2849 16.7329C37.8251 17.0502 38.4238 17.208 39.0794 17.208C39.735 17.208 40.3368 17.0502 40.8847 16.7329C41.431 16.4157 41.8666 15.9561 42.1882 15.3557C42.5099 14.7537 42.6715 14.0527 42.6715 13.2496C42.6715 12.4464 42.5099 11.7485 42.1882 11.1543Z" fill="#1c1c1c"/><path d="M46.7239 10.3682C47.161 9.54646 47.7689 8.9089 48.5476 8.45703C49.3264 8.00362 50.2175 7.77769 51.2209 7.77769C52.5214 7.77769 53.5926 8.09492 54.4344 8.72939C55.2763 9.36385 55.8334 10.2428 56.1043 11.3694H54.2128C54.0327 10.7225 53.6818 10.2119 53.1616 9.83583C52.6399 9.46135 51.9935 9.27255 51.2209 9.27255C50.2175 9.27255 49.4064 9.61919 48.7893 10.3109C48.1721 11.0026 47.8628 11.9837 47.8628 13.2511C47.8628 14.5185 48.1721 15.5213 48.7893 16.2207C49.4064 16.9202 50.2175 17.2684 51.2209 17.2684C51.9935 17.2684 52.6368 17.0873 53.1509 16.7252C53.6649 16.3631 54.0189 15.8447 54.2128 15.1731H56.1043C55.8211 16.2594 55.2547 17.1306 54.4052 17.7837C53.5556 18.4367 52.4937 18.7632 51.2209 18.7632C50.2175 18.7632 49.3264 18.5373 48.5476 18.0839C47.7689 17.6305 47.161 16.9898 46.7239 16.1619C46.2868 15.334 46.0683 14.3638 46.0683 13.2511C46.0683 12.1385 46.2868 11.1914 46.7239 10.3697" fill="#1c1c1c"/><path d="M60.1964 9.40715V15.676C60.1964 16.1944 60.3056 16.5596 60.5242 16.7731C60.7427 16.9867 61.1229 17.0935 61.6631 17.0935H62.9558V18.5883H61.3737C60.3949 18.5883 59.6623 18.3624 59.1729 17.909C58.6835 17.4556 58.4388 16.7128 58.4388 15.6775V9.40869H57.0691V7.95252H58.4388V5.27383H60.1948V7.95252H62.9543V9.40869H60.1948L60.1964 9.40715Z" fill="#1c1c1c"/><path d="M64.752 5.87423C64.5196 5.64211 64.4042 5.35737 64.4042 5.02002C64.4042 4.68267 64.5196 4.39948 64.752 4.16581C64.9844 3.93214 65.2661 3.81608 65.6016 3.81608C65.9371 3.81608 66.1972 3.93214 66.4219 4.16581C66.6466 4.39948 66.7605 4.68422 66.7605 5.02002C66.7605 5.35582 66.6481 5.64056 66.4219 5.87423C66.1972 6.1079 65.9232 6.22396 65.6016 6.22396C65.2799 6.22396 64.9844 6.1079 64.752 5.87423ZM66.4511 18.5868H64.6951V7.95095H66.4511V18.5868Z" fill="#1c1c1c"/><path d="M73.2443 16.9573L76.527 7.95096H78.3985L74.2493 18.5868H72.2024L68.0531 7.95096H69.9446L73.2443 16.9573Z" fill="#1c1c1c"/><path d="M88.8608 13.9289H80.4069C80.4716 14.9766 80.8286 15.7952 81.4781 16.3848C82.1275 16.9744 82.9155 17.2684 83.842 17.2684C84.6008 17.2684 85.2348 17.0904 85.7427 16.7345C86.2506 16.3786 86.6076 15.9035 86.8139 15.3077H88.7053C88.4222 16.3306 87.8558 17.1616 87.0063 17.8023C86.1567 18.4429 85.1009 18.7632 83.8405 18.7632C82.837 18.7632 81.9398 18.5373 81.1472 18.0839C80.3561 17.6305 79.7344 16.9867 79.285 16.1526C78.834 15.3186 78.6093 14.3514 78.6093 13.2511C78.6093 12.1509 78.8279 11.1868 79.265 10.3589C79.702 9.53098 80.3161 8.89342 81.1087 8.44775C81.8998 8.00207 82.8109 7.77769 83.8405 7.77769C84.8701 7.77769 85.7319 7.99743 86.5045 8.43691C87.2771 8.8764 87.8712 9.48146 88.2898 10.2521C88.7084 11.0212 88.9177 11.8924 88.9177 12.8627C88.9177 13.2001 88.8977 13.5544 88.8592 13.9305M86.66 10.755C86.3645 10.2691 85.9613 9.90083 85.4534 9.64859C84.9455 9.39635 84.3822 9.26946 83.7651 9.26946C82.8771 9.26946 82.1214 9.55419 81.4965 10.1237C80.8717 10.6931 80.5146 11.4824 80.4254 12.4913H87.1032C87.1032 11.8182 86.9555 11.2394 86.66 10.755Z" fill="#1c1c1c"/><path d="M92.3343 18.3439C91.6909 18.0653 91.1831 17.6784 90.8091 17.1801C90.4351 16.6819 90.2304 16.1093 90.1919 15.4624H92.0064C92.0572 15.9932 92.305 16.4265 92.7498 16.7623C93.1946 17.0997 93.7763 17.2668 94.4966 17.2668C95.1661 17.2668 95.694 17.1183 96.0787 16.8196C96.465 16.5225 96.6574 16.1464 96.6574 15.6946C96.6574 15.2427 96.4512 14.8821 96.0402 14.6562C95.6278 14.4303 94.9906 14.2074 94.1288 13.9862C93.3439 13.7788 92.7036 13.5683 92.2081 13.3548C91.7125 13.1412 91.2877 12.824 90.9337 12.4046C90.5798 11.9837 90.4028 11.4313 90.4028 10.7457C90.4028 10.2026 90.5628 9.70428 90.886 9.25087C91.2077 8.79746 91.6648 8.43844 92.2558 8.17382C92.8483 7.90921 93.5224 7.77612 94.2827 7.77612C95.4539 7.77612 96.3988 8.07324 97.1206 8.66902C97.8409 9.2648 98.2272 10.0788 98.2795 11.114H96.5235C96.485 10.5585 96.2634 10.1113 95.8571 9.77546C95.4523 9.43966 94.9075 9.27099 94.2257 9.27099C93.5947 9.27099 93.093 9.40716 92.7206 9.67797C92.3466 9.95033 92.1603 10.3063 92.1603 10.7457C92.1603 11.0955 92.2727 11.3833 92.4989 11.6092C92.7236 11.8352 93.0068 12.0162 93.3485 12.1524C93.6901 12.2886 94.1626 12.4402 94.7675 12.6089C95.5262 12.8163 96.1449 13.0205 96.6204 13.2202C97.096 13.4213 97.5054 13.7215 97.8455 14.1223C98.1856 14.5231 98.3626 15.0477 98.3765 15.6946C98.3765 16.2764 98.2149 16.801 97.8932 17.2668C97.5716 17.7326 97.1175 18.0978 96.5327 18.3624C95.9479 18.627 95.2753 18.7601 94.5151 18.7601C93.704 18.7601 92.9776 18.6209 92.3343 18.3423" fill="#1c1c1c"/><path d="M102.603 9.40715V15.676C102.603 16.1944 102.712 16.5596 102.931 16.7731C103.149 16.9867 103.529 17.0935 104.069 17.0935H105.362V18.5883H103.779C102.801 18.5883 102.067 18.3624 101.578 17.909C101.088 17.4556 100.844 16.7128 100.844 15.6775V9.40869H99.4724V7.95252H100.844V5.27383H102.6V7.95252H105.361V9.40869H102.6L102.603 9.40715Z" fill="#1c1c1c"/><path d="M106.713 10.3682C107.15 9.54646 107.752 8.91044 108.519 8.45703C109.284 8.00362 110.136 7.77769 111.077 7.77769C112.017 7.77769 112.806 7.97886 113.49 8.37966C114.171 8.78045 114.679 9.28493 115.015 9.89309V7.95255H116.791V18.5884H115.015V16.6091C114.667 17.2297 114.15 17.745 113.46 18.152C112.773 18.559 111.971 18.7632 111.058 18.7632C110.145 18.7632 109.27 18.5296 108.509 18.0638C107.751 17.598 107.152 16.945 106.715 16.1031C106.278 15.2628 106.059 14.305 106.059 13.231C106.059 12.1571 106.278 11.1899 106.715 10.3682M114.532 11.1543C114.21 10.5601 113.776 10.1035 113.228 9.78632C112.682 9.46908 112.08 9.31124 111.423 9.31124C110.766 9.31124 110.168 9.46599 109.628 9.77703C109.088 10.0881 108.657 10.5415 108.335 11.1357C108.014 11.7315 107.852 12.4294 107.852 13.231C107.852 14.0326 108.012 14.7553 108.335 15.3557C108.657 15.9577 109.088 16.4173 109.628 16.7329C110.168 17.0502 110.767 17.208 111.423 17.208C112.078 17.208 112.68 17.0502 113.228 16.7329C113.774 16.4157 114.21 15.9561 114.532 15.3557C114.853 14.7537 115.015 14.0527 115.015 13.2496C115.015 12.4464 114.853 11.7485 114.532 11.1543Z" fill="#1c1c1c"/><path d="M121.519 9.40715V15.676C121.519 16.1944 121.628 16.5596 121.847 16.7731C122.065 16.9867 122.445 17.0935 122.986 17.0935H124.278V18.5883H122.695C121.717 18.5883 120.983 18.3624 120.494 17.909C120.004 17.4556 119.76 16.7128 119.76 15.6775V9.40869H118.388V7.95252H119.76V5.27383H121.516V7.95252H124.277V9.40869H121.516L121.519 9.40715Z" fill="#1c1c1c"/><path d="M135.222 13.9289H126.768C126.833 14.9766 127.19 15.7952 127.839 16.3848C128.489 16.9744 129.277 17.2684 130.203 17.2684C130.962 17.2684 131.596 17.0904 132.104 16.7345C132.612 16.3786 132.969 15.9035 133.175 15.3077H135.067C134.784 16.3306 134.217 17.1616 133.368 17.8023C132.518 18.4429 131.462 18.7632 130.202 18.7632C129.198 18.7632 128.301 18.5373 127.509 18.0839C126.718 17.6305 126.096 16.9867 125.646 16.1526C125.195 15.3186 124.971 14.3514 124.971 13.2511C124.971 12.1509 125.189 11.1868 125.626 10.3589C126.063 9.53098 126.679 8.89342 127.47 8.44775C128.261 8.00207 129.172 7.77769 130.202 7.77769C131.232 7.77769 132.093 7.99743 132.866 8.43691C133.639 8.8764 134.233 9.48146 134.651 10.2521C135.07 11.0212 135.279 11.8924 135.279 12.8627C135.279 13.2001 135.259 13.5544 135.221 13.9305M133.023 10.755C132.727 10.2691 132.324 9.90083 131.816 9.64859C131.308 9.39635 130.745 9.26946 130.128 9.26946C129.24 9.26946 128.484 9.55419 127.86 10.1237C127.235 10.6931 126.878 11.4824 126.788 12.4913H133.466C133.466 11.8182 133.318 11.2394 133.023 10.755Z" fill="#1c1c1c"/></g></svg>'''

COMMON_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Poppins', sans-serif; background: #f5f9ff; color: #141429; min-height: 100vh; font-size: 14px; }

  /* nav */
  .nav { background: #fff; border-bottom: 1px solid #ebebeb; padding: 0 32px; height: 61px; display: flex; align-items: center; gap: 24px; box-shadow: 0 1px 4px rgba(18,87,178,.06); position: sticky; top: 0; z-index: 40; }
  .nav-logo { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .nav-divider { width: 1px; height: 20px; background: #d1d1d6; }
  .nav-title { font-size: 15px; font-weight: 600; color: #141429; }
  .nav-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
  .nav-badge { background: #e4efff; color: #1257b2; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 43px; white-space: nowrap; }
  .nav-link { font-size: 13px; color: #1257b2; text-decoration: none; border: 1px solid #c4dcf9; padding: 6px 16px; border-radius: 6px; font-weight: 600; transition: background .15s; white-space: nowrap; }
  .nav-link:hover { background: #e4efff; }

  /* toolbar */
  .toolbar { padding: 20px 32px 0; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
  .search-wrap { position: relative; flex: 1; min-width: 200px; max-width: 460px; }
  .search-wrap svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #8c8c9a; pointer-events: none; }
  .search-wrap input { width: 100%; padding: 9px 12px 9px 38px; background: #fff; border: 1px solid #dadada; border-radius: 8px; color: #141429; font-family: 'Poppins', sans-serif; font-size: 13px; outline: none; transition: border-color .15s, box-shadow .15s; }
  .search-wrap input:focus { border-color: #1257b2; box-shadow: 0 0 0 3px rgba(18,87,178,.1); }
  .search-wrap input::placeholder { color: #8c8c9a; }
  .count-label { font-size: 12px; color: #8c8c9a; white-space: nowrap; }
  .count-label b { color: #141429; }
  .generated { font-size: 11px; color: #8c8c9a; margin-left: auto; }

  /* card + table */
  .card { background: #fff; border: 1px solid #ebebeb; border-radius: 12px; margin: 16px 32px 40px; overflow: hidden; box-shadow: 0 2px 8px rgba(18,87,178,.06); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th { text-align: left; padding: 11px 16px; background: #f5f9ff; color: #8c8c9a; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; border-bottom: 1px solid #ebebeb; cursor: pointer; user-select: none; white-space: nowrap; }
  thead th:hover { color: #1257b2; }
  thead th.sorted { color: #1257b2; }
  thead th .arr { display: inline-block; margin-left: 4px; opacity: .5; }
  thead th.sorted .arr { opacity: 1; }
  tbody tr { border-bottom: 1px solid #f0f0f0; transition: background .1s; }
  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: #f5f9ff; }
  tbody td { padding: 11px 16px; vertical-align: middle; }
  .td-idx { color: #8c8c9a; font-size: 11px; }
  td.pkg-name { font-family: ui-monospace, 'Cascadia Code', monospace; font-size: 12px; color: #1257b2; white-space: nowrap; }
  td.pkg-name a { color: inherit; text-decoration: none; }
  td.pkg-name a:hover { text-decoration: underline; }

  /* version pills */
  .vpill { display: inline-block; background: #f5f9ff; border: 1px solid #c4dcf9; color: #1257b2; font-family: ui-monospace, monospace; font-size: 11px; padding: 1px 8px; border-radius: 4px; margin: 2px 2px 2px 0; white-space: nowrap; }
  .vpill.latest { background: #e4efff; border-color: #1257b2; font-weight: 600; }
  .no-version { color: #8c8c9a; font-size: 11px; font-style: italic; }

  /* filter buttons */
  .filter-btns { display: flex; gap: 8px; }
  .fbtn { padding: 6px 14px; border-radius: 6px; border: 1px solid #dadada; background: #fff; color: #8c8c9a; font-family: 'Poppins', sans-serif; font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; }
  .fbtn:hover { border-color: #1257b2; color: #1257b2; background: #f5f9ff; }
  .fbtn.active { background: #e4efff; border-color: #1257b2; color: #1257b2; }

  /* stat cards */
  .stats { display: flex; gap: 16px; padding: 20px 32px 0; flex-wrap: wrap; }
  .stat { background: #fff; border: 1px solid #ebebeb; border-radius: 10px; padding: 16px 24px; min-width: 140px; box-shadow: 0 1px 4px rgba(18,87,178,.05); }
  .stat .slabel { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: #8c8c9a; margin-bottom: 8px; }
  .stat .svalue { font-size: 28px; font-weight: 600; line-height: 1; color: #141429; }
  .stat.blue  .svalue { color: #1257b2; }
  .stat.red   .svalue { color: #d93025; }
  .stat.amber .svalue { color: #b45309; }
  .stat.green .svalue { color: #16a34a; }

  /* cve-specific */
  td.vuln-id { font-family: ui-monospace, monospace; font-size: 11px; color: #b45309; white-space: nowrap; }
  td.cve-col { font-family: ui-monospace, monospace; font-size: 11px; }
  .cvepill { display: inline-block; background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; font-size: 10px; padding: 1px 7px; border-radius: 4px; margin: 1px 2px 1px 0; white-space: nowrap; }
  .fix-col { font-family: ui-monospace, monospace; font-size: 11px; color: #16a34a; white-space: nowrap; }
  .no-fix { color: #8c8c9a; font-size: 11px; font-style: italic; }
  .status-ok   { display:inline-block; background:#f0fdf4; border:1px solid #bbf7d0; color:#16a34a; font-size:11px; font-weight:600; padding:2px 10px; border-radius:4px; }
  .status-vuln { display:inline-block; background:#fef2f2; border:1px solid #fecaca; color:#d93025; font-size:11px; font-weight:600; padding:2px 10px; border-radius:4px; }
  td.desc-col  { font-size:12px; color:#555; max-width:400px; line-height:1.5; }
  td.ver-col   { font-family:ui-monospace,monospace; font-size:11px; color:#141429; white-space:nowrap; }

  /* empty state */
  #empty-state { text-align: center; padding: 80px 32px; color: #8c8c9a; display: none; }
  #empty-state h3 { font-size: 15px; font-weight: 600; color: #141429; margin-bottom: 6px; }

  @media (max-width: 640px) {
    .nav, .toolbar, .stats, .card { padding-left: 16px; padding-right: 16px; }
    .card { margin-left: 16px; margin-right: 16px; }
  }
"""

SEARCH_ICON = '''<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>'''

# ── index.html ────────────────────────────────────────────────────────────────

def build_index():
    with open(DATA_JSON) as f:
        data = json.load(f)
    packages = data["packages"]
    total = len(packages)
    generated = datetime.datetime.fromisoformat(data["generated"].rstrip("Z")).strftime("Updated %b %d, %Y %H:%M UTC")
    data_json = json.dumps(packages, separators=(",", ":")).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Curated Catalog — ActiveState</title>
  <style>{COMMON_CSS}</style>
</head>
<body>

<nav class="nav">
  <div class="nav-logo">{LOGO_SVG}</div>
  <div class="nav-divider"></div>
  <span class="nav-title">Curated Catalog</span>
  <div class="nav-right">
    <span class="nav-badge">{total:,} packages</span>
    <a class="nav-link" href="scan_report.html">CVE Report</a>
  </div>
</nav>

<div class="toolbar">
  <div class="search-wrap">
    {SEARCH_ICON}
    <input id="search" type="text" placeholder="Search packages&#x2026;" autocomplete="off">
  </div>
  <div class="count-label">Showing <b id="shown-count">{total:,}</b> of <b>{total:,}</b></div>
  <div class="generated">{generated}</div>
</div>

<div class="card">
  <table id="pkg-table">
    <thead>
      <tr>
        <th class="td-idx" style="width:48px">#</th>
        <th data-col="name" class="sorted">Package <span class="arr">&#x2191;</span></th>
        <th data-col="count" style="width:72px">Count <span class="arr"></span></th>
        <th>Versions</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="empty-state">
    <h3>No packages found</h3>
    <p>Try a different search term.</p>
  </div>
</div>

<script>
const INDEX_URL = "https://repo.activestate.com/b4ef73d0-2ca1-40cf-8f55-b742bf8088c7/pypi/simple/";
const ALL = {data_json};
let sortCol = "name", sortDir = 1;

function esc(s) {{ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }}

function render(pkgs) {{
  const tbody = document.getElementById("tbody");
  const empty = document.getElementById("empty-state");
  const tbl   = document.getElementById("pkg-table");
  document.getElementById("shown-count").textContent = pkgs.length.toLocaleString();
  if (!pkgs.length) {{ tbl.style.display="none"; empty.style.display="block"; return; }}
  tbl.style.display="table"; empty.style.display="none";
  tbody.innerHTML = pkgs.map((p,i) => {{
    const url = INDEX_URL + p.name + "/";
    const pills = p.versions.length === 0
      ? '<span class="no-version">—</span>'
      : p.versions.map((v,vi) =>
          '<span class="vpill' + (vi===p.versions.length-1?' latest':'') + '">' + esc(v) + '</span>'
        ).join("");
    return '<tr>'
      + '<td class="td-idx">'+(i+1)+'</td>'
      + '<td class="pkg-name"><a href="'+url+'" target="_blank" rel="noopener">'+esc(p.name)+'</a></td>'
      + '<td class="td-idx" style="text-align:center">'+p.versions.length+'</td>'
      + '<td>'+pills+'</td></tr>';
  }}).join("");
}}

function go() {{
  const q = document.getElementById("search").value.trim().toLowerCase();
  let res = q ? ALL.filter(p=>p.name.toLowerCase().includes(q)) : ALL;
  res = [...res].sort((a,b) => {{
    const av = sortCol==="name" ? a.name.toLowerCase() : a.versions.length;
    const bv = sortCol==="name" ? b.name.toLowerCase() : b.versions.length;
    return av<bv ? -sortDir : av>bv ? sortDir : 0;
  }});
  render(res);
}}

document.querySelectorAll("thead th[data-col]").forEach(th => {{
  th.addEventListener("click", () => {{
    sortDir = sortCol===th.dataset.col ? sortDir*-1 : 1;
    sortCol = th.dataset.col;
    document.querySelectorAll("thead th").forEach(t => {{
      t.classList.remove("sorted");
      const a=t.querySelector(".arr"); if(a) a.textContent="";
    }});
    th.classList.add("sorted");
    const a=th.querySelector(".arr"); if(a) a.textContent=sortDir===1?"↑":"↓";
    go();
  }});
}});
let t; document.getElementById("search").addEventListener("input",()=>{{clearTimeout(t);t=setTimeout(go,150);}});
go();
</script>
</body>
</html>"""


# ── scan_report.html ──────────────────────────────────────────────────────────

def build_report():
    with open(AUDIT_JSON) as f:
        raw = json.load(f)
    deps = raw if isinstance(raw, list) else raw.get("dependencies", [])

    scanned = []
    for dep in deps:
        findings = []
        for v in dep.get("vulns", []):
            aliases = v.get("aliases", [])
            cves = [a for a in aliases if a.startswith("CVE-")]
            findings.append({
                "id":  v.get("id", ""),
                "cves": cves,
                "fix":  v.get("fix_versions", []),
                "description": v.get("description", ""),
            })
        scanned.append({"name": dep.get("name",""), "version": dep.get("version",""), "vulns": findings})

    total   = len(scanned)
    vuln_n  = sum(1 for p in scanned if p["vulns"])
    cve_n   = sum(len(p["vulns"]) for p in scanned)
    clean_n = total - vuln_n
    generated = datetime.datetime.utcnow().strftime("Generated %b %d, %Y %H:%M UTC")
    data_json = json.dumps(scanned, separators=(",", ":")).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CVE Scan Report — ActiveState</title>
  <style>{COMMON_CSS}</style>
</head>
<body>

<nav class="nav">
  <div class="nav-logo">{LOGO_SVG}</div>
  <div class="nav-divider"></div>
  <span class="nav-title">CVE Scan Report</span>
  <div class="nav-right">
    <a class="nav-link" href="index.html">&#8592; Package Catalog</a>
  </div>
</nav>

<div class="stats">
  <div class="stat blue"><div class="slabel">Packages Scanned</div><div class="svalue">{total:,}</div></div>
  <div class="stat {'red' if vuln_n else 'green'}"><div class="slabel">Vulnerable</div><div class="svalue">{vuln_n}</div></div>
  <div class="stat {'amber' if cve_n else 'green'}"><div class="slabel">Total CVEs</div><div class="svalue">{cve_n}</div></div>
  <div class="stat green"><div class="slabel">Clean</div><div class="svalue">{clean_n}</div></div>
  <div class="stat" style="margin-left:auto;min-width:auto">
    <div class="slabel">Scanner</div>
    <div class="svalue" style="font-size:13px;font-weight:600;color:#8c8c9a;padding-top:6px">pip-audit · OSV</div>
  </div>
</div>

<div class="toolbar" style="margin-top:0">
  <div class="search-wrap">
    {SEARCH_ICON}
    <input id="search" type="text" placeholder="Search packages&#x2026;" autocomplete="off">
  </div>
  <div class="filter-btns">
    <button class="fbtn active" data-f="all">All</button>
    <button class="fbtn" data-f="vuln">Vulnerable</button>
    <button class="fbtn" data-f="clean">Clean</button>
  </div>
  <div class="count-label">Showing <b id="shown-count">—</b> rows</div>
  <div class="generated">{generated}</div>
</div>

<div class="card">
  <table id="rpt-table">
    <thead>
      <tr>
        <th class="td-idx" style="width:40px">#</th>
        <th>Package</th>
        <th style="width:110px">Version</th>
        <th style="width:90px">Status</th>
        <th style="width:160px">Vuln ID</th>
        <th style="width:160px">CVE Aliases</th>
        <th style="width:120px">Fix Version</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="empty-state">
    <h3>No results match your filter</h3>
    <p>Try a different search or filter.</p>
  </div>
</div>

<script>
const ALL = {data_json};
let activeF = "all";

function esc(s) {{ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }}

function buildRows(pkgs) {{
  const rows = [];
  let n = 0;
  pkgs.forEach(p => {{
    if (!p.vulns.length) {{
      n++;
      rows.push('<tr data-s="clean">'
        +'<td class="td-idx">'+n+'</td>'
        +'<td class="pkg-name">'+esc(p.name)+'</td>'
        +'<td class="ver-col">'+esc(p.version)+'</td>'
        +'<td><span class="status-ok">Clean</span></td>'
        +'<td>—</td><td>—</td><td>—</td>'
        +'<td class="desc-col" style="color:#8c8c9a">No known vulnerabilities</td>'
        +'</tr>');
    }} else {{
      p.vulns.forEach((v,vi) => {{
        n++;
        const cveTags = v.cves.length
          ? v.cves.map(c=>'<span class="cvepill">'+esc(c)+'</span>').join("")
          : '<span style="color:#8c8c9a">—</span>';
        const fixStr = v.fix.length
          ? v.fix.map(f=>esc(f)).join(", ")
          : '<span class="no-fix">No fix available</span>';
        const desc = v.description.length>280
          ? esc(v.description.slice(0,280))+'&#x2026;'
          : esc(v.description);
        rows.push('<tr data-s="vuln">'
          +'<td class="td-idx">'+n+'</td>'
          +'<td class="pkg-name">'+(vi===0?esc(p.name):'')+'</td>'
          +'<td class="ver-col">'+(vi===0?esc(p.version):'')+'</td>'
          +'<td>'+(vi===0?'<span class="status-vuln">Vulnerable</span>':'')+'</td>'
          +'<td class="vuln-id">'+esc(v.id)+'</td>'
          +'<td class="cve-col">'+cveTags+'</td>'
          +'<td class="fix-col">'+fixStr+'</td>'
          +'<td class="desc-col">'+desc+'</td>'
          +'</tr>');
      }});
    }}
  }});
  return rows;
}}

function go() {{
  const q = document.getElementById("search").value.trim().toLowerCase();
  let res = ALL;
  if (q) res = res.filter(p=>p.name.toLowerCase().includes(q));
  if (activeF==="vuln")  res = res.filter(p=>p.vulns.length>0);
  if (activeF==="clean") res = res.filter(p=>p.vulns.length===0);
  const rows = buildRows(res);
  const tbl = document.getElementById("rpt-table");
  const empty = document.getElementById("empty-state");
  if (!rows.length) {{ tbl.style.display="none"; empty.style.display="block"; document.getElementById("shown-count").textContent="0"; return; }}
  tbl.style.display="table"; empty.style.display="none";
  document.getElementById("tbody").innerHTML = rows.join("");
  document.getElementById("shown-count").textContent = rows.length.toLocaleString();
}}

document.querySelectorAll(".fbtn").forEach(b => {{
  b.addEventListener("click", () => {{
    document.querySelectorAll(".fbtn").forEach(x=>x.classList.remove("active"));
    b.classList.add("active"); activeF=b.dataset.f; go();
  }});
}});
let t; document.getElementById("search").addEventListener("input",()=>{{clearTimeout(t);t=setTimeout(go,150);}});
go();
</script>
</body>
</html>"""


# ── write ─────────────────────────────────────────────────────────────────────

idx  = build_index()
rpt  = build_report()

with open(os.path.join(ROOT, "index.html"), "w") as f: f.write(idx)
with open(os.path.join(ROOT, "scan_report.html"), "w") as f: f.write(rpt)

print(f"index.html       {len(idx)//1024} KB")
print(f"scan_report.html {len(rpt)//1024} KB")
print("Done — open either file directly in your browser.")
