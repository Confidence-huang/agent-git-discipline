// commitlint 配置（自包含：刻意不 extends @commitlint/config-conventional）
//
// 为什么不 extends：CI 里用 `npx @commitlint/cli` 临时拉包，仓库本身没有 node_modules，
// `extends` 指向的配置包在仓库侧解析不到，会直接报错。把规则写在这里最稳。
// 依据：docs/05 §四 的标题规范；docs/06 §五 说明为何"免费仓库只能用 CI 强制提交信息"。
export default {
  rules: {
    'type-empty': [2, 'never'],
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新增能力 / 规则
        'fix',      // 修复错误行为
        'docs',     // 仅文档
        'chore',    // 杂项、依赖、格式化
        'refactor', // 不改行为的重构
        'test',     // 测试
        'ci',       // 工作流、门禁、构建
        'build',    // 构建产物与打包
        'perf',     // 性能
        'backup',   // 本项目自定义：快照刷新（bak-local-archives 用它）
      ],
    ],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 100],
    'body-leading-blank': [1, 'always'],
  },
};
