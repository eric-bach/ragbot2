(globalThis.TURBOPACK = globalThis.TURBOPACK || []).push([typeof document === "object" ? document.currentScript : undefined, {

"[project]/app/(home)/layout.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "default": ()=>RootLayout
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$components$2f$Authenticator$2f$Authenticator$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react/dist/esm/components/Authenticator/Authenticator.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Button$2f$Button$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react/dist/esm/primitives/Button/Button.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Heading$2f$Heading$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react/dist/esm/primitives/Heading/Heading.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Image$2f$Image$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react/dist/esm/primitives/Image/Image.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$components$2f$ThemeProvider$2f$ThemeProvider$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react/dist/esm/components/ThemeProvider/ThemeProvider.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2d$core$2f$dist$2f$esm$2f$Authenticator$2f$hooks$2f$useAuthenticator$2f$useAuthenticator$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__useAuthenticator$3e$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react-core/dist/esm/Authenticator/hooks/useAuthenticator/useAuthenticator.mjs [app-client] (ecmascript) <export default as useAuthenticator>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$hooks$2f$useTheme$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react/dist/esm/hooks/useTheme.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$View$2f$View$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@aws-amplify/ui-react/dist/esm/primitives/View/View.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$aws$2d$amplify$2f$dist$2f$esm$2f$initSingleton$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__DefaultAmplify__as__Amplify$3e$__ = __turbopack_context__.i("[project]/node_modules/aws-amplify/dist/esm/initSingleton.mjs [app-client] (ecmascript) <export DefaultAmplify as Amplify>");
;
var _s = __turbopack_context__.k.signature();
'use client';
;
;
;
const config = {
    Auth: {
        Cognito: {
            userPoolId: ("TURBOPACK compile-time value", "us-west-2_PKZyGibSP"),
            userPoolClientId: ("TURBOPACK compile-time value", "3v9uf5cigt2j413rp151i9d2hk")
        }
    }
};
__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$aws$2d$amplify$2f$dist$2f$esm$2f$initSingleton$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__DefaultAmplify__as__Amplify$3e$__["Amplify"].configure(config, {
    ssr: true
});
function RootLayout(param) {
    let { children } = param;
    _s();
    const { tokens } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$hooks$2f$useTheme$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTheme"])();
    const theme = {
        name: 'Auth Theme',
        tokens: {
            components: {
                authenticator: {
                    router: {
                        boxShadow: "0 0 16px ".concat(tokens.colors.overlay['10']),
                        borderWidth: '0'
                    },
                    form: {
                        padding: "".concat(tokens.space.medium, " ").concat(tokens.space.xl, " ").concat(tokens.space.medium)
                    }
                },
                button: {
                    primary: {
                        backgroundColor: '#0067c0'
                    },
                    link: {
                        color: '#0067c0'
                    }
                },
                fieldcontrol: {
                    _focus: {
                        boxShadow: "0 0 0 2px #0067c0"
                    }
                },
                tabs: {
                    item: {
                        color: tokens.colors.neutral['80'],
                        _active: {
                            borderColor: tokens.colors.neutral['100'],
                            color: '#0067c0'
                        }
                    }
                }
            }
        }
    };
    const components = {
        Header () {
            const { tokens } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$hooks$2f$useTheme$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTheme"])();
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$View$2f$View$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["View"], {
                textAlign: "center",
                padding: tokens.space.large,
                paddingTop: "6rem",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Image$2f$Image$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Image"], {
                        alt: "RAGBot 2",
                        src: "logo.jpg",
                        width: 54
                    }, void 0, false, {
                        fileName: "[project]/app/(home)/layout.tsx",
                        lineNumber: 82,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Heading$2f$Heading$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Heading"], {
                        level: 4,
                        children: "RAGBot 2"
                    }, void 0, false, {
                        fileName: "[project]/app/(home)/layout.tsx",
                        lineNumber: 83,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/(home)/layout.tsx",
                lineNumber: 81,
                columnNumber: 9
            }, this);
        },
        SignIn: {
            Header () {
                const { tokens } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$hooks$2f$useTheme$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTheme"])();
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Heading$2f$Heading$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Heading"], {
                    padding: "".concat(tokens.space.xl, " 0 0 ").concat(tokens.space.xl),
                    level: 4,
                    children: "Sign in to your account"
                }, void 0, false, {
                    fileName: "[project]/app/(home)/layout.tsx",
                    lineNumber: 93,
                    columnNumber: 11
                }, this);
            },
            Footer () {
                const { toForgotPassword } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2d$core$2f$dist$2f$esm$2f$Authenticator$2f$hooks$2f$useAuthenticator$2f$useAuthenticator$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__useAuthenticator$3e$__["useAuthenticator"])();
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$View$2f$View$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["View"], {
                    textAlign: "center",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Button$2f$Button$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                        fontWeight: "normal",
                        onClick: toForgotPassword,
                        size: "small",
                        variation: "link",
                        children: "Reset Password"
                    }, void 0, false, {
                        fileName: "[project]/app/(home)/layout.tsx",
                        lineNumber: 103,
                        columnNumber: 13
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/app/(home)/layout.tsx",
                    lineNumber: 102,
                    columnNumber: 11
                }, this);
            }
        },
        SignUp: {
            Header () {
                const { tokens } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$hooks$2f$useTheme$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTheme"])();
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Heading$2f$Heading$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Heading"], {
                    padding: "".concat(tokens.space.xl, " 0 0 ").concat(tokens.space.xl),
                    level: 4,
                    children: "Create a new account"
                }, void 0, false, {
                    fileName: "[project]/app/(home)/layout.tsx",
                    lineNumber: 116,
                    columnNumber: 11
                }, this);
            },
            Footer () {
                const { toSignIn } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2d$core$2f$dist$2f$esm$2f$Authenticator$2f$hooks$2f$useAuthenticator$2f$useAuthenticator$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__useAuthenticator$3e$__["useAuthenticator"])();
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$View$2f$View$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["View"], {
                    textAlign: "center",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$primitives$2f$Button$2f$Button$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Button"], {
                        fontWeight: "normal",
                        onClick: toSignIn,
                        size: "small",
                        variation: "link",
                        children: "Back to Sign In"
                    }, void 0, false, {
                        fileName: "[project]/app/(home)/layout.tsx",
                        lineNumber: 126,
                        columnNumber: 13
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/app/(home)/layout.tsx",
                    lineNumber: 125,
                    columnNumber: 11
                }, this);
            }
        }
    };
    const formFields = {
        signUp: {
            username: {
                label: 'Email:',
                placeholder: 'Enter your email',
                order: 1
            },
            password: {
                order: 2
            },
            confirm_password: {
                order: 3
            }
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$components$2f$ThemeProvider$2f$ThemeProvider$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ThemeProvider"], {
        theme: theme,
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$components$2f$Authenticator$2f$Authenticator$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Authenticator"], {
            formFields: formFields,
            components: components,
            children: (param)=>{
                let { signOut, user } = param;
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
                    children: children
                }, void 0, false, {
                    fileName: "[project]/app/(home)/layout.tsx",
                    lineNumber: 154,
                    columnNumber: 33
                }, this);
            }
        }, void 0, false, {
            fileName: "[project]/app/(home)/layout.tsx",
            lineNumber: 153,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/app/(home)/layout.tsx",
        lineNumber: 152,
        columnNumber: 5
    }, this);
}
_s(RootLayout, "k2qWeHbN6Sg+sHb/2RjMBdCAyA8=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$aws$2d$amplify$2f$ui$2d$react$2f$dist$2f$esm$2f$hooks$2f$useTheme$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTheme"]
    ];
});
_c = RootLayout;
var _c;
__turbopack_context__.k.register(_c, "RootLayout");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
}]);

//# sourceMappingURL=app_%28home%29_layout_tsx_5e91e859._.js.map