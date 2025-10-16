export default {
  testEnvironment: 'jest-environment-node',
  transform: {
    '^.+\\.[jt]sx?$': ['babel-jest', { presets: [['@babel/preset-env', { targets: { node: 'current' } }]] }],
  },
  setupFiles: ['./jest.setup.js'],
};
