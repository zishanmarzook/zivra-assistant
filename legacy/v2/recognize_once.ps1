# Runs only after the user presses LISTEN. Uses built-in Windows Speech recognition if installed.
$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Speech
    $recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $choices = New-Object System.Speech.Recognition.Choices
    $phrases = @(
        'hey zivra open spotify','hey zivra open chrome','hey zivra open files',
        'hey zivra open settings','hey zivra open chatgpt','hey zivra open ghostlink',
        'hey zivra open instagram','hey zivra open phone link',
        'hey zivra system status','hey zivra pause music','hey zivra next song',
        'hey zivra previous song','hey zivra volume up','hey zivra volume down',
        'hey zivra mute','hey zivra help',
        'open spotify','open chrome','open files','open settings','open chatgpt',
        'open ghostlink','open instagram','open phone link','system status',
        'pause music','next song','previous song','volume up','volume down',
        'mute','help'
    )
    $choices.Add([string[]]$phrases)
    $builder = New-Object System.Speech.Recognition.GrammarBuilder
    $builder.Append($choices)
    $grammar = New-Object System.Speech.Recognition.Grammar($builder)
    $recognizer.LoadGrammar($grammar)
    $recognizer.SetInputToDefaultAudioDevice()
    $result = $recognizer.Recognize([TimeSpan]::FromSeconds(8))
    if ($null -ne $result -and $result.Confidence -ge 0.42) {
        [Console]::WriteLine('RESULT::' + $result.Text)
    } else {
        [Console]::WriteLine('ERROR::No command recognized. Check microphone permission or try typing.')
    }
} catch {
    [Console]::WriteLine('ERROR::Windows offline speech recognition is not available. Install an English speech recognizer in Windows settings, or use Win+H in the command box. ' + $_.Exception.Message)
    exit 1
} finally {
    if ($null -ne $recognizer) { $recognizer.Dispose() }
}
