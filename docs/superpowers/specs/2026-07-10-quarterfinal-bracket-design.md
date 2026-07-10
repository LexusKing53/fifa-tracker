# Quarterfinal-Only Bracket Design

## Scope

The Bracket page starts at the confirmed quarterfinal stage. The Predictions page,
its match catalog, and saved prediction data are out of scope and must remain
unchanged.

## Quarterfinals

The bracket displays these four editable matches:

1. France vs Morocco
2. Spain vs Belgium
3. Norway vs England
4. Argentina vs Switzerland

## Advancement

The semifinal preview is always visible and pairs the winners of quarterfinals
1 and 2, then 3 and 4. Once all quarterfinal winners are chosen, the semifinal
winner controls become editable. The third-place playoff and final remain
visible as previews and become editable after both semifinal winners are known.

## Persistence And Safety

Existing Round of 32 and Round of 16 bracket records are neither displayed nor
deleted. Quarterfinal and later bracket selections continue using the existing
bracket persistence store. No prediction-store behavior or prediction-page code
is changed.

## Verification

Regression tests will prove that the Bracket page has no Round of 32 or Round
of 16 rendering, includes the four confirmed quarterfinals, and retains
semifinal/final advancement. Prediction-page isolation will be checked by a
static regression test and the full test suite.
