// https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts
const sub = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
'x': 'ₓ', 'X': 'ₓ', 'y': 'ᵧ', 'Y': 'ᵧ', "+": "₊", "-": "₋", 'm': 'ₘ', 'n': 'ₙ', 'Д': 'д', 'д': 'д', 'i': 'ᵢ', 'j': 'ⱼ'}
const sup = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
'x': 'ˣ', 'X': 'ˣ', 'y': 'ʸ', 'Y': 'ʸ', '+': '⁺', '-': '⁻', 'm': 'ᵐ', 'n': 'ⁿ'}

sups = document.getElementsByTagName("sup")
subs = document.getElementsByTagName("sub")

for (const tag of sups) {
    text = tag.innerHTML
    tag.innerHTML = ""
    for (const s in text) {
        tag.innerHTML = tag.innerHTML + sup[text[s]]
    }
}

for (const tag of subs) {
    text = tag.innerHTML
    tag.innerHTML = ""
    for (const s in text) {
        tag.innerHTML = tag.innerHTML + sub[text[s]]
    }
}