from android.content import Intent
from android.net import Uri


def restart_app(activity):
    from android.app import AlarmManager, PendingIntent
    from android.content import Context
    from android.os import Process
    from java import cast
    from java.lang import System
    context = activity.getApplicationContext()
    intent = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName())
    if intent is None:
        raise RuntimeError('launch intent not found')
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK)
    pending = PendingIntent.getActivity(context, 0, intent,
                                        PendingIntent.FLAG_CANCEL_CURRENT | PendingIntent.FLAG_IMMUTABLE)
    alarm = cast(AlarmManager, context.getSystemService(Context.ALARM_SERVICE))
    alarm.set(AlarmManager.RTC, System.currentTimeMillis() + 400, pending)
    Process.killProcess(Process.myPid())


def open_url(activity, url):
    activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
