// INTENTIONALLY VULNERABLE — AI / training fixture only.
const { graphql, buildSchema } = require('graphql');

const schema = buildSchema(`
  type Query {
    node(id: ID!): Node
    root: Node
  }
  type Node {
    id: ID!
    children(depth: Int!): [Node]
  }
`);
