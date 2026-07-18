#include <linux/module.h>
#include <linux/hid.h>

extern struct hid_driver razer_kbd_driver;
extern struct hid_driver razer_mouse_driver;
extern struct hid_driver razer_accessory_driver;
extern struct hid_driver razer_kraken_driver;

static int __init razer_dfuse_init(void)
{
    int ret;

    ret = hid_register_driver(&razer_kbd_driver);
    if (ret)
        return ret;

    ret = hid_register_driver(&razer_mouse_driver);
    if (ret)
        goto unregister_kbd;

    ret = hid_register_driver(&razer_accessory_driver);
    if (ret)
        goto unregister_mouse;

    ret = hid_register_driver(&razer_kraken_driver);
    if (ret)
        goto unregister_accessory;

    return 0;

unregister_accessory:
    hid_unregister_driver(&razer_accessory_driver);
unregister_mouse:
    hid_unregister_driver(&razer_mouse_driver);
unregister_kbd:
    hid_unregister_driver(&razer_kbd_driver);

    return ret;
}

static void __exit razer_dfuse_exit(void)
{
    hid_unregister_driver(&razer_kraken_driver);
    hid_unregister_driver(&razer_accessory_driver);
    hid_unregister_driver(&razer_mouse_driver);
    hid_unregister_driver(&razer_kbd_driver);
}

module_init(razer_dfuse_init);
module_exit(razer_dfuse_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DFUSE");
MODULE_DESCRIPTION("DFUSE bundled OpenRazer HID drivers");
